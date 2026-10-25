import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

TMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TMP_MEDIA)
class UploadApiTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def post(self, name, data=b"hello world", ctype="application/octet-stream"):
        return self.client.post("/api/uploads/", {"file": SimpleUploadedFile(name, data, ctype)}, format="multipart")

    def test_txt_is_extracted(self):
        r = self.post("note.txt")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["modality"], "document")
        self.assertEqual(r.data["status"], "processed")

    def test_image_is_stored_without_handler(self):
        r = self.post("scan.png", b"\x89PNG fake")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["modality"], "image")
        self.assertEqual(r.data["status"], "stored")

    def test_audio_is_stored_without_handler(self):
        r = self.post("memo.mp3", b"ID3 fake")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["modality"], "audio")

    def test_unsupported_type_rejected(self):
        self.assertEqual(self.post("virus.exe").status_code, 400)

    def test_empty_file_rejected(self):
        self.assertEqual(self.post("empty.txt", b"").status_code, 400)

    def test_list_filter_and_delete(self):
        a = self.post("a.txt").data["id"]
        self.post("b.png", b"x")
        self.assertEqual(len(self.client.get("/api/uploads/").data), 2)
        self.assertEqual(len(self.client.get("/api/uploads/?modality=image").data), 1)
        self.assertEqual(self.client.delete(f"/api/uploads/{a}/").status_code, 204)
        self.assertEqual(len(self.client.get("/api/uploads/").data), 1)
