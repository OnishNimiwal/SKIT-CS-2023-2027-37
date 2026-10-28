# Dashboard + Multimodal Upload: integration steps

## Backend (Django)
1. Copy `backend/uploads/` into your repo's `backend/` folder (next to `chat/` and `documents/`).
2. `backend/config/settings.py`:
   ```python
   INSTALLED_APPS += ["uploads"]
   # Optional: plug in your own OCR / speech-to-text (each takes a file path, returns text)
   # UPLOAD_OCR_HANDLER        = "OCR_modul.<your_module>.<your_function>"
   # UPLOAD_TRANSCRIBE_HANDLER = "voice_search.<your_module>.<your_function>"
   ```
3. `backend/config/urls.py`: add `path("api/uploads/", include("uploads.urls")),`
   (make sure MEDIA_URL / MEDIA_ROOT are set and media is served in DEBUG, as for documents).
4. Run:
   ```bash
   ./env/bin/python backend/manage.py migrate
   ./env/bin/python backend/manage.py test uploads
   ```

## Frontend (React)
Copy everything under `frontend/src/` (keep the folder structure), then:
- Replace your `App.jsx` with the shell in `App.example.jsx` (see the notes at its bottom about the chat page).
- No new npm packages are needed (uses lucide-react, already in your project).

## Notes
- Old files `api/uploadFile.js` and `components/documents/MultiFileUpload.*` (previous step) are not used by the
  dashboard. Keep or delete them.
- Navigation uses URL hashes (`#/uploads`), so there is no react-router dependency.
