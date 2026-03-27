import { useEffect, useState } from "react";
import { getAIConfig, updateAIConfig, getRAGConfig, updateRAGConfig } from "../../api/admin";
import type { AIConfig } from "../../types/admin";

const MODELS = [
  "claude-sonnet-4-20250514",
  "claude-opus-4-20250514",
  "claude-haiku-4-5-20251001",
];

export function AISettingsPage() {
  const [configs, setConfigs] = useState<AIConfig[]>([]);
  const [ragConfig, setRagConfig] = useState<Record<string, Record<string, unknown>>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getAIConfig(), getRAGConfig()])
      .then(([ai, rag]) => {
        setConfigs(ai);
        setRagConfig(rag as Record<string, Record<string, unknown>>);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function handleAIConfigUpdate(key: string, value: unknown) {
    setSaving(key);
    try {
      await updateAIConfig(key, { value });
      setConfigs((prev) =>
        prev.map((c) => (c.key === key ? { ...c, value: { value } } : c))
      );
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(null);
    }
  }

  async function handleRAGConfigUpdate(key: string, value: unknown) {
    setSaving(`rag-${key}`);
    try {
      const valueKey = key === "embedding_model" ? "value" : key === "chunk_size" || key === "chunk_overlap" ? "tokens" : "value";
      await updateRAGConfig(key, { [valueKey]: value });
      setRagConfig((prev) => ({
        ...prev,
        [key]: { [valueKey]: value },
      }));
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(null);
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-gray-400">Loading...</div>;
  }

  const getConfigValue = (key: string): unknown => {
    const config = configs.find((c) => c.key === key);
    return config?.value?.value ?? config?.value;
  };

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">AI Settings</h1>

      {/* AI Model Settings */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Model Configuration</h2>
        <div className="space-y-6">
          {/* Model */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Migration Model
            </label>
            <select
              value={(getConfigValue("model") as string) || MODELS[0]}
              onChange={(e) => handleAIConfigUpdate("model", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              {MODELS.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          {/* Temperature */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Temperature: {(getConfigValue("temperature") as number) || 0.3}
            </label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={(getConfigValue("temperature") as number) || 0.3}
              onChange={(e) => handleAIConfigUpdate("temperature", parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>Deterministic</span>
              <span>Creative</span>
            </div>
          </div>

          {/* Max Tokens */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Tokens
            </label>
            <input
              type="number"
              min={256}
              max={16384}
              value={(getConfigValue("max_tokens") as number) || 4096}
              onChange={(e) => handleAIConfigUpdate("max_tokens", parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>

          {/* Classification Model */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Classification Model (for auto-detection)
            </label>
            <select
              value={(getConfigValue("classification_model") as string) || MODELS[2]}
              onChange={(e) => handleAIConfigUpdate("classification_model", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              {MODELS.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* RAG Settings */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">RAG Configuration</h2>
        <div className="space-y-6">
          {/* Chunk Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Chunk Size (tokens)
            </label>
            <input
              type="number"
              min={128}
              max={2048}
              value={(ragConfig.chunk_size?.tokens as number) || 512}
              onChange={(e) => handleRAGConfigUpdate("chunk_size", parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>

          {/* Chunk Overlap */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Chunk Overlap (tokens)
            </label>
            <input
              type="number"
              min={0}
              max={512}
              value={(ragConfig.chunk_overlap?.tokens as number) || 64}
              onChange={(e) => handleRAGConfigUpdate("chunk_overlap", parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>

          {/* Top K */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Top K (results per query)
            </label>
            <input
              type="number"
              min={1}
              max={20}
              value={(ragConfig.top_k?.value as number) || 5}
              onChange={(e) => handleRAGConfigUpdate("top_k", parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>

          {/* Similarity Threshold */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Similarity Threshold: {(ragConfig.similarity_threshold?.value as number) || 0.75}
            </label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={(ragConfig.similarity_threshold?.value as number) || 0.75}
              onChange={(e) => handleRAGConfigUpdate("similarity_threshold", parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-400">
              <span>More results (less relevant)</span>
              <span>Fewer results (more relevant)</span>
            </div>
          </div>
        </div>
      </div>

      {saving && (
        <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">
          Saving {saving}...
        </div>
      )}
    </div>
  );
}
