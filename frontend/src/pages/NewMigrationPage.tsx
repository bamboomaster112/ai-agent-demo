import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { CodeEditor } from "../components/CodeEditor";
import { FileUploader } from "../components/FileUploader";
import { DetectionBadge } from "../components/DetectionBadge";
import { detectPipeline } from "../api/detection";
import { createSession } from "../api/migrations";
import type { DetectionResult, SourceType } from "../types/migration";

const SOURCE_OPTIONS: { value: SourceType; label: string }[] = [
  { value: "jenkins", label: "Jenkins (Groovy Jenkinsfile)" },
  { value: "teamcity_kotlin", label: "TeamCity (Kotlin DSL)" },
  { value: "teamcity_xml", label: "TeamCity (XML)" },
  { value: "teamcity_json", label: "TeamCity (JSON API)" },
];

export function NewMigrationPage() {
  const navigate = useNavigate();
  const [sourceType, setSourceType] = useState<SourceType>("jenkins");
  const [code, setCode] = useState("");
  const [title, setTitle] = useState("");
  const [files, setFiles] = useState<Array<{ file: File; preview?: string }>>([]);
  const [detection, setDetection] = useState<DetectionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleDetect() {
    if (!code.trim()) return;
    try {
      const result = await detectPipeline(code);
      setDetection(result);
      // Auto-set source type based on detection
      const formatToSource: Record<string, SourceType> = {
        groovy: "jenkins",
        kotlin_dsl: "teamcity_kotlin",
        xml: "teamcity_xml",
        json_api: "teamcity_json",
      };
      if (formatToSource[result.source_format]) {
        setSourceType(formatToSource[result.source_format]);
      }
    } catch (err) {
      console.error("Detection failed:", err);
    }
  }

  async function handleStartMigration() {
    if (!code.trim()) {
      setError("Please paste your pipeline code");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const session = await createSession(sourceType, code, title || undefined);
      navigate(`/migrate/${session.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create session");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">New Migration</h1>

      <div className="space-y-6">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Migration Title (optional)
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Backend CI Pipeline"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Source Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Source Type
          </label>
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value as SourceType)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {SOURCE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Code Input */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-sm font-medium text-gray-700">
              Pipeline Code
            </label>
            <button
              onClick={handleDetect}
              disabled={!code.trim()}
              className="text-sm text-blue-600 hover:text-blue-700 disabled:text-gray-400"
            >
              Auto-detect type
            </button>
          </div>
          <CodeEditor
            value={code}
            onChange={setCode}
            language={sourceType === "jenkins" ? "groovy" : sourceType.includes("xml") ? "xml" : "kotlin"}
            placeholder="Paste your Jenkinsfile, TeamCity Kotlin DSL, XML config, or JSON API output..."
          />
        </div>

        {/* Detection Result */}
        {detection && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm font-medium text-blue-800 mb-2">
              Auto-Detection Result:
            </p>
            <DetectionBadge
              platform={detection.source_platform}
              format={detection.source_format}
              configType={detection.config_type}
              confidence={detection.confidence}
              method={detection.method}
            />
          </div>
        )}

        {/* File Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Screenshots & Config Files (optional)
          </label>
          <FileUploader files={files} onFilesChange={setFiles} />
        </div>

        {/* Error */}
        {error && (
          <div className="p-3 bg-red-50 text-red-600 rounded-md text-sm">
            {error}
          </div>
        )}

        {/* Submit */}
        <button
          onClick={handleStartMigration}
          disabled={loading || !code.trim()}
          className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Creating migration..." : "Start Migration"}
        </button>
      </div>
    </div>
  );
}
