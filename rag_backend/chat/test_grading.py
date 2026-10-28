from django.test import SimpleTestCase

from .grading import clean_query, decide_next_step, grade_chunks


class GradeChunksTests(SimpleTestCase):
    def test_empty(self):
        self.assertEqual(grade_chunks([], good_score=0.4), "empty")

    def test_weak(self):
        self.assertEqual(grade_chunks([{"score": 0.35}], good_score=0.4), "weak")

    def test_good_uses_best_score(self):
        self.assertEqual(grade_chunks([{"score": 0.9}, {"score": 0.1}], good_score=0.4), "good")


class DecideNextStepTests(SimpleTestCase):
    def test_good_always_generates(self):
        self.assertEqual(decide_next_step("good", 0, 1), "generate")
        self.assertEqual(decide_next_step("good", 5, 1), "generate")

    def test_retries_when_not_good_and_attempts_left(self):
        self.assertEqual(decide_next_step("weak", 0, 1), "rewrite")
        self.assertEqual(decide_next_step("empty", 0, 1), "rewrite")

    def test_after_retries_weak_generates_and_empty_not_found(self):
        self.assertEqual(decide_next_step("weak", 1, 1), "generate")
        self.assertEqual(decide_next_step("empty", 1, 1), "not_found")

    def test_retries_disabled(self):
        self.assertEqual(decide_next_step("empty", 0, 0), "not_found")
        self.assertEqual(decide_next_step("weak", 0, 0), "generate")


class CleanQueryTests(SimpleTestCase):
    def test_strips_quotes(self):
        self.assertEqual(clean_query('"warranty period"', "x"), "warranty period")

    def test_strips_label_and_extra_lines(self):
        self.assertEqual(clean_query("Search query: warranty period\nextra", "x"), "warranty period")

    def test_falls_back_when_empty(self):
        self.assertEqual(clean_query("", "original"), "original")
        self.assertEqual(clean_query("   \n  ", "original"), "original")

    def test_limits_length(self):
        self.assertLessEqual(len(clean_query("a" * 500, "x")), 200)