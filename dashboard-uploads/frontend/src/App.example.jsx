// Example App.jsx. Replace your current tab switcher with this shell.
// Pages you already have are plugged into `routes`; see the notes below.
import DashboardLayout from './components/dashboard/DashboardLayout';
import OverviewPage from './pages/OverviewPage';
import UploadCenterPage from './pages/UploadCenterPage';
import DocumentsPage from './components/documents/DocumentsPage'; // existing component
// import ChatPage from './pages/ChatPage';                       // see note 1

export default function App() {
  return (
    <DashboardLayout
      routes={{
        overview: <OverviewPage />,
        chat: <p>Move your existing chat view here (note 1).</p>, // replace with <ChatPage />
        documents: <DocumentsPage />,
        uploads: <UploadCenterPage />,
      }}
    />
  );
}

/*
 Note 1: Your current App.jsx holds the chat state (messages, send handler) next to the
 tab switcher. Move that state + <ChatWindow/> + <MessageInput/> into a new
 pages/ChatPage.jsx component, then use <ChatPage /> above.
 Note 2: If DocumentsPage needs props, pass them here as you did before.
*/
