import { useState } from 'react';
import MultimodalUpload from '../components/uploads/MultimodalUpload';
import UploadLibrary from '../components/uploads/UploadLibrary';

export default function UploadCenterPage() {
  const [refreshKey, setRefreshKey] = useState(0);
  return (
    <div className="grid-2">
      <div className="card"><MultimodalUpload onUploaded={() => setRefreshKey((k) => k + 1)} /></div>
      <div className="card"><UploadLibrary refreshKey={refreshKey} /></div>
    </div>
  );
}
