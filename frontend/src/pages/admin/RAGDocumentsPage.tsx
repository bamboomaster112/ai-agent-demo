import { useEffect, useState } from "react";
import { Trash2, Upload, Search } from "lucide-react";
import { apiFetch } from "../../api/client";

interface Document {
  id: string;
  doc_type: string;
  source_platform: string | null;
  title: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export function RAGDocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<unknown[]>([]);

  const [newDoc, setNewDoc] = useState({
    doc_type: "reference_doc",
    title: "",
    content: "",
    source_platform: "",
  });

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    try {
      const data = await apiFetch<Document[]>("/api/rag/documents");
      setDocuments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload() {
    try {
      await apiFetch("/api/rag/documents", {
        method: "POST",
        body: JSON.stringify(newDoc),
      });
      setShowUpload(false);
      setNewDoc({ doc_type: "reference_doc", title: "", content: "", source_platform: "" });
      loadDocuments();
    } catch (err) {
      console.error(err);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this document and all its chunks?")) return;
    try {
      await apiFetch(`/api/rag/documents/${id}`, { method: "DELETE" });
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      console.error(err);
    }
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    try {
      const result = await apiFetch<{ results: unknown[] }>("/api/rag/search", {
        method: "POST",
        body: JSON.stringify({ query: searchQuery }),
      });
      setSearchResults(result.results);
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">RAG Documents</h1>
        <button
          onClick={() => setShowUpload(true)}
          className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
        >
          <Upload className="h-4 w-4" />
          Upload Document
        </button>
      </div>

      {/* Search */}
      <div className="mb-6 flex gap-2">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Test semantic search..."
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
        />
        <button
          onClick={handleSearch}
          className="flex items-center gap-2 px-4 py-2 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
        >
          <Search className="h-4 w-4" />
          Search
        </button>
      </div>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-semibold text-blue-800 mb-2">Search Results</h3>
          {searchResults.map((r: any, i: number) => (
            <div key={i} className="mb-2 p-2 bg-white rounded text-sm">
              <p className="text-gray-700">{r.content?.slice(0, 200)}...</p>
              <p className="text-xs text-gray-400 mt-1">
                Similarity: {(r.similarity * 100).toFixed(1)}%
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Upload form */}
      {showUpload && (
        <div className="mb-6 p-4 bg-white border border-gray-200 rounded-lg space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <select
              value={newDoc.doc_type}
              onChange={(e) => setNewDoc({ ...newDoc, doc_type: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="reference_doc">Reference Doc</option>
              <option value="actions_doc">GitHub Actions Doc</option>
              <option value="pipeline_config">Pipeline Config</option>
            </select>
            <input
              type="text"
              placeholder="Title"
              value={newDoc.title}
              onChange={(e) => setNewDoc({ ...newDoc, title: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
            <select
              value={newDoc.source_platform}
              onChange={(e) => setNewDoc({ ...newDoc, source_platform: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="">Any Platform</option>
              <option value="teamcity">TeamCity</option>
              <option value="jenkins">Jenkins</option>
            </select>
          </div>
          <textarea
            placeholder="Document content (Markdown, configs, etc.)"
            value={newDoc.content}
            onChange={(e) => setNewDoc({ ...newDoc, content: e.target.value })}
            rows={8}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
          />
          <div className="flex gap-2">
            <button
              onClick={handleUpload}
              disabled={!newDoc.content}
              className="px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              Upload & Index
            </button>
            <button
              onClick={() => setShowUpload(false)}
              className="px-3 py-2 text-gray-600 hover:text-gray-900 text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Documents list */}
      {loading ? (
        <div className="text-center py-8 text-gray-400">Loading...</div>
      ) : documents.length === 0 ? (
        <div className="text-center py-12 bg-white border border-gray-200 rounded-lg">
          <p className="text-gray-500">No documents indexed</p>
        </div>
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-lg"
            >
              <div className="flex-1">
                <h3 className="font-medium text-gray-900">{doc.title || "Untitled"}</h3>
                <div className="flex gap-2 mt-1">
                  <span className="px-2 py-0.5 bg-gray-50 text-gray-600 rounded text-xs">
                    {doc.doc_type}
                  </span>
                  {doc.source_platform && (
                    <span className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs">
                      {doc.source_platform}
                    </span>
                  )}
                </div>
              </div>
              <span className="text-xs text-gray-400">
                {new Date(doc.created_at).toLocaleDateString()}
              </span>
              <button
                onClick={() => handleDelete(doc.id)}
                className="p-2 text-gray-400 hover:text-red-500"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
