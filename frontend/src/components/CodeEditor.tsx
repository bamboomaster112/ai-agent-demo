import { useState } from "react";

interface Props {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  placeholder?: string;
  readOnly?: boolean;
}

export function CodeEditor({
  value,
  onChange,
  language = "text",
  placeholder = "Paste your pipeline code here...",
  readOnly = false,
}: Props) {
  return (
    <div className="relative h-full min-h-[300px]">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        readOnly={readOnly}
        placeholder={placeholder}
        className="w-full h-full min-h-[300px] p-4 font-mono text-sm bg-gray-900 text-green-400 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
        spellCheck={false}
      />
      {language && (
        <span className="absolute top-2 right-2 text-xs text-gray-500 bg-gray-800 px-2 py-1 rounded">
          {language}
        </span>
      )}
    </div>
  );
}
