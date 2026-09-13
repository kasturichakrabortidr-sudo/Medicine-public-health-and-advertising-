import { Link, Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import Methods from "./pages/Methods";
import DeckPage from "./pages/DeckPage";
import RunBrief from "./pages/RunBrief";

export default function App() {
  return (
    <Routes>
      <Route path="/deck" element={<DeckPage />} />
      <Route path="/deck/:runId" element={<DeckPage />} />
      <Route
        path="*"
        element={
          <>
            <nav className="site-nav">
              <Link className="brand" to="/">
                Evidence Workflow
              </Link>
              <Link to="/">Home</Link>
              <Link to="/methods">Methods</Link>
              <Link to="/run">New brief</Link>
              <Link to="/deck">Open deck</Link>
            </nav>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/methods" element={<Methods />} />
              <Route path="/run" element={<RunBrief />} />
            </Routes>
          </>
        }
      />
    </Routes>
  );
}
