"""Tests for SakSit Thai/English Bilingual Tone and GEO Evaluator."""

from __future__ import annotations

import unittest

from sakthai.agent.editorial_eval import (
    EditorialEvalResult,
    evaluate_editorial_quality,
)


class TestBilingualEditorialEval(unittest.TestCase):
    def test_authentic_thai_content_scores_high_tone(self) -> None:
        content = """# เปิดตัวโมเดลใหม่: House of Sak Thai Decision v1
โมเดลภาษาไทยขนาดเล็ก ใช้งานฟรี รันโลคอล 100% ไม่ต้องใช้การ์ดจอแพง ไม่มีค่าใช้จ่าย

### สรุปความสามารถ
- ประหยัดต้นทุน รันได้บนเครื่องตัวเอง
- ติดตั้งง่าย โอเพนซอร์ส
- รองรับงาน MLOps ครบวงจร
"""
        result: EditorialEvalResult = evaluate_editorial_quality(content)
        self.assertTrue(result.is_bilingual or result.thai_tone_score > 0.0)
        self.assertGreaterEqual(result.thai_tone_score, 80.0)
        self.assertTrue(result.is_publishable)
        self.assertIn(result.grade, ("S", "A"))

    def test_robotic_machine_translation_thai_penalized(self) -> None:
        content = """# รายงานระบบ
โมเดลนี้ถูกกระทำโดยทีมงาน และมีความจำเป็นต้องกระทำตามคำสั่ง ในท้ายที่สุดของวัน มันเป็นสิ่งสำคัญที่จะบันทึกไว้ว่าระบบทำงานได้
"""
        result: EditorialEvalResult = evaluate_editorial_quality(content)
        self.assertLess(result.thai_tone_score, 60.0)
        self.assertFalse(result.is_publishable)
        self.assertTrue(
            any(
                "machine-translation" in f.lower() or "unnatural" in f.lower()
                for f in result.findings
            )
        )

    def test_bilingual_mixed_content_detection(self) -> None:
        content = """# Release v2.65.0: SakThai Core
House of Sak ขอแนะนำโมเดลภาษาไทยรุ่นใหม่ ใช้งานฟรี รันโลคอล ไม่มีค่าใช้จ่าย

### Technical Metrics
- Inference latency: 12ms
- License: Apache 2.0 (โอเพนซอร์ส)
- Zero financial spend ($0.00 USD)
"""
        result: EditorialEvalResult = evaluate_editorial_quality(content)
        self.assertTrue(result.is_bilingual)
        self.assertGreaterEqual(result.thai_tone_score, 85.0)
        self.assertGreaterEqual(result.total_score, 75.0)
        self.assertTrue(result.is_publishable)

    def test_pure_english_content_preserves_zero_thai_score(self) -> None:
        content = """# Pure English Release
This release includes only English technical documentation without Thai characters.
- Fast inference
- Low latency
"""
        result: EditorialEvalResult = evaluate_editorial_quality(content)
        self.assertFalse(result.is_bilingual)
        self.assertEqual(result.thai_tone_score, 0.0)


if __name__ == "__main__":
    unittest.main()
