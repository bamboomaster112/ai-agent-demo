import { useState } from "react";
import { Copy, Download, Check } from "lucide-react";

interface Props {
  filename: string;
  content: string;
  notes?: Array<{ level: string; text: string }>;
}

export function YamlPreview({ filename, content, notes = [] }: Props) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownload() {
    const blob = new Blob([content], { type: "text/yaml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename.split("/").pop() || "workflow.yml";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
        <span className="text-sm font-mono text-gray-600">{filename}</span>
        <div className="flex gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:text-gray-900 bg-white border border-gray-300 rounded"
          >
            {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            {copied ? "Copied" : "Copy"}
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:text-gray-900 bg-white border border-gray-300 rounded"
          >
            <Download className="h-3 w-3" />
            Download
          </button>
        </div>
      </div>

      {/* Content */}
      <pre className="p-4 text-sm font-mono bg-gray-900 text-green-400 overflow-auto max-h-[500px]">
        <code>{content}</code>
      </pre>

      {/* Notes */}
      {notes.length > 0 && (
        <div className="p-3 bg-yellow-50 border-t border-yellow-200 space-y-1">
          {notes.map((note, i) => (
            <p
              key={i}
              className={`text-xs ${
                note.level === "warning" ? "text-orange-700" : "text-blue-700"
              }`}
            >
              <span className="font-semibold uppercase">{note.level}: </span>
              {note.text}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
