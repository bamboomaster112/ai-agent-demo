import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, X, Image, FileCode } from "lucide-react";

interface UploadedFile {
  file: File;
  preview?: string;
}

interface Props {
  files: UploadedFile[];
  onFilesChange: (files: UploadedFile[]) => void;
  accept?: Record<string, string[]>;
}

export function FileUploader({ files, onFilesChange, accept }: Props) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newFiles = acceptedFiles.map((file) => ({
        file,
        preview: file.type.startsWith("image/")
          ? URL.createObjectURL(file)
          : undefined,
      }));
      onFilesChange([...files, ...newFiles]);
    },
    [files, onFilesChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: accept || {
      "image/*": [".png", ".jpg", ".jpeg", ".gif", ".webp"],
      "text/*": [".txt", ".xml", ".groovy", ".kts"],
      "application/json": [".json"],
    },
    maxSize: 10 * 1024 * 1024,
  });

  function removeFile(index: number) {
    const updated = [...files];
    if (updated[index].preview) {
      URL.revokeObjectURL(updated[index].preview!);
    }
    updated.splice(index, 1);
    onFilesChange(updated);
  }

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition ${
          isDragActive
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 hover:border-gray-400"
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="h-8 w-8 mx-auto text-gray-400 mb-2" />
        <p className="text-sm text-gray-600">
          {isDragActive
            ? "Drop files here..."
            : "Drag & drop files, or click to browse"}
        </p>
        <p className="text-xs text-gray-400 mt-1">
          Screenshots, config files (max 10MB)
        </p>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((f, i) => (
            <div
              key={i}
              className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg"
            >
              {f.preview ? (
                <img
                  src={f.preview}
                  alt={f.file.name}
                  className="h-10 w-10 object-cover rounded"
                />
              ) : (
                <FileCode className="h-10 w-10 text-gray-400 p-2" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-700 truncate">{f.file.name}</p>
                <p className="text-xs text-gray-400">
                  {(f.file.size / 1024).toFixed(1)} KB
                </p>
              </div>
              <button
                onClick={() => removeFile(i)}
                className="p-1 text-gray-400 hover:text-red-500"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
