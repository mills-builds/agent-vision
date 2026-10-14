import unittest

from agent_vision import hx_bus
from agent_vision.cli import plan_goto


class PacketTests(unittest.TestCase):
    def test_checksum(self):
        # ID 1, LEN 3, CMD 28: ~(32) & 0xFF = 0xDF
        self.assertEqual(hx_bus.checksum(bytes([1, 3, 28])), 0xDF)

    def test_build_read(self):
        self.assertEqual(hx_bus.build_packet(1, hx_bus.POS_READ), bytes([0x55, 0x55, 1, 3, 28, 0xDF]))

    def test_build_unload(self):
        p = hx_bus.build_packet(2, hx_bus.UNLOAD, [0])
        self.assertEqual(p[:6], bytes([0x55, 0x55, 2, 4, 31, 0]))
        self.assertEqual(p[6], (~(2 + 4 + 31)) & 0xFF)

    def test_move_packet(self):
        p = hx_bus.move_packet(3, 500, 1000)
        self.assertEqual(p[2:9], bytes([3, 7, 1, 500 & 0xFF, 500 >> 8, 1000 & 0xFF, 1000 >> 8]))
        self.assertEqual(p[-1], hx_bus.checksum(p[2:-1]))

    def test_move_packet_clamps_to_servo_range(self):
        self.assertEqual(hx_bus.move_packet(1, 1500, 100)[5:7], bytes([1000 & 0xFF, 1000 >> 8]))
        self.assertEqual(hx_bus.move_packet(1, -5, 100)[5:7], bytes([0, 0]))

    def test_parse_reply(self):
        reply = hx_bus.build_packet(1, hx_bus.POS_READ, (612).to_bytes(2, "little"))
        frames, left = hx_bus.parse_frames(b"\x00junk" + reply)
        self.assertEqual(frames, [(1, 28, (612).to_bytes(2, "little"))])
        self.assertEqual(left, b"")

    def test_parse_echo_then_reply(self):
        echo = hx_bus.build_packet(4, hx_bus.TEMP_READ)
        reply = hx_bus.build_packet(4, hx_bus.TEMP_READ, [41])
        frames, _ = hx_bus.parse_frames(echo + reply)
        self.assertEqual(frames, [(4, 26, b""), (4, 26, bytes([41]))])

    def test_parse_bad_checksum_skipped(self):
        bad = bytearray(hx_bus.build_packet(1, 28, b"\x10\x00"))
        bad[-1] ^= 0xFF
        self.assertEqual(hx_bus.parse_frames(bytes(bad))[0], [])

    def test_parse_partial(self):
        reply = hx_bus.build_packet(1, 28, b"\x10\x00")
        frames, left = hx_bus.parse_frames(reply[:5])
        self.assertEqual(frames, [])
        self.assertEqual(left, reply[:5])


class ClampTests(unittest.TestCase):
    def test_clamp(self):
        self.assertEqual(hx_bus.clamp(5, 10, 20), 10)
        self.assertEqual(hx_bus.clamp(25, 10, 20), 20)
        self.assertEqual(hx_bus.clamp(15, 10, 20), 15)

    def test_margin(self):
        self.assertEqual(hx_bus.apply_margin(100, 900, 25), (125, 875))

    def test_margin_never_inverts(self):
        a, b = hx_bus.apply_margin(100, 130, 25)
        self.assertLessEqual(a, b)

    def test_plan_goto_clamps_and_steps(self):
        limits = {1: (100, 900), 2: (200, 800)}
        clamped, wps = plan_goto({1: 500, 2: 500}, {1: 950, 2: 100}, limits, max_step=20)
        self.assertEqual(clamped, {1: 900, 2: 200})
        self.assertEqual(wps[-1], clamped)
        prev = {1: 500, 2: 500}
        for wp in wps:
            for s in wp:
                self.assertLessEqual(abs(wp[s] - prev[s]), 20)
                self.assertTrue(limits[s][0] <= wp[s] <= limits[s][1])
            prev = wp

    def test_resolve_port_priority(self):
        import os
        old = os.environ.pop("AV_PORT", None)
        try:
            self.assertEqual(hx_bus.resolve_port("/dev/a", {"port": "/dev/c"}), "/dev/a")
            self.assertEqual(hx_bus.resolve_port(None, {"port": "/dev/c"}), "/dev/c")
            os.environ["AV_PORT"] = "/dev/b"
            self.assertEqual(hx_bus.resolve_port(None, {"port": "/dev/c"}), "/dev/b")
            with self.assertRaises(SystemExit):
                del os.environ["AV_PORT"]
                hx_bus.resolve_port(None, {})
        finally:
            if old is not None:
                os.environ["AV_PORT"] = old


if __name__ == "__main__":
    unittest.main()
