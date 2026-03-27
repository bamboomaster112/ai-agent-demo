import { useEffect, useState } from "react";
import { Plus, Trash2, Edit2, Save, X } from "lucide-react";
import {
  listPreferences,
  createPreference,
  updatePreference,
  deletePreference,
} from "../api/preferences";
import type { Preference } from "../types/admin";

export function PreferencesPage() {
  const [prefs, setPrefs] = useState<Preference[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [newPref, setNewPref] = useState({
    category: "general",
    key: "",
    value: "",
  });

  useEffect(() => {
    loadPrefs();
  }, []);

  async function loadPrefs() {
    try {
      const data = await listPreferences();
      setPrefs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd() {
    if (!newPref.key || !newPref.value) return;
    try {
      await createPreference(newPref.category, newPref.key, newPref.value);
      setShowAdd(false);
      setNewPref({ category: "general", key: "", value: "" });
      loadPrefs();
    } catch (err) {
      console.error(err);
    }
  }

  async function handleUpdate(id: string) {
    try {
      await updatePreference(id, editValue);
      setEditingId(null);
      loadPrefs();
    } catch (err) {
      console.error(err);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Remove this preference?")) return;
    try {
      await deletePreference(id);
      setPrefs((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      console.error(err);
    }
  }

  const categories = [...new Set(prefs.map((p) => p.category))];

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Preferences</h1>
          <p className="text-sm text-gray-500 mt-1">
            The AI agent remembers these preferences across migrations
          </p>
        </div>
        <button
          onClick={() => setShowAdd(true)}
          className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Add Preference
        </button>
      </div>

      {/* Add form */}
      {showAdd && (
        <div className="mb-6 p-4 bg-white border border-gray-200 rounded-lg space-y-3">
          <div className="grid grid-cols-3 gap-3">
            <select
              value={newPref.category}
              onChange={(e) => setNewPref({ ...newPref, category: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="general">General</option>
              <option value="runner_image">Runner Image</option>
              <option value="build_strategy">Build Strategy</option>
              <option value="tooling">Tooling</option>
              <option value="style">Style</option>
            </select>
            <input
              type="text"
              placeholder="Key (e.g., default_runner)"
              value={newPref.key}
              onChange={(e) => setNewPref({ ...newPref, key: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
            <input
              type="text"
              placeholder="Value (e.g., ubuntu-22.04)"
              value={newPref.value}
              onChange={(e) => setNewPref({ ...newPref, value: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleAdd}
              className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            >
              Add
            </button>
            <button
              onClick={() => setShowAdd(false)}
              className="px-3 py-1 text-gray-600 hover:text-gray-900 text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-400">Loading...</div>
      ) : prefs.length === 0 ? (
        <div className="text-center py-12 bg-white border border-gray-200 rounded-lg">
          <p className="text-gray-500">No preferences saved yet</p>
          <p className="text-sm text-gray-400 mt-1">
            The AI agent will learn your preferences from conversations
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {categories.map((cat) => (
            <div key={cat}>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                {cat.replace(/_/g, " ")}
              </h3>
              <div className="space-y-2">
                {prefs
                  .filter((p) => p.category === cat)
                  .map((pref) => (
                    <div
                      key={pref.id}
                      className="flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-lg"
                    >
                      <div className="flex-1">
                        <span className="text-sm font-medium text-gray-700">
                          {pref.preference_key}
                        </span>
                        {editingId === pref.id ? (
                          <input
                            type="text"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            className="ml-2 px-2 py-1 border border-gray-300 rounded text-sm"
                          />
                        ) : (
                          <span className="ml-2 text-sm text-gray-500">
                            = {pref.preference_value}
                          </span>
                        )}
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded text-xs ${
                          pref.source === "explicit"
                            ? "bg-green-50 text-green-700"
                            : pref.source === "inferred"
                              ? "bg-purple-50 text-purple-700"
                              : "bg-gray-50 text-gray-700"
                        }`}
                      >
                        {pref.source}
                      </span>
                      <div className="flex gap-1">
                        {editingId === pref.id ? (
                          <>
                            <button
                              onClick={() => handleUpdate(pref.id)}
                              className="p-1 text-green-600 hover:text-green-700"
                            >
                              <Save className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => setEditingId(null)}
                              className="p-1 text-gray-400 hover:text-gray-600"
                            >
                              <X className="h-4 w-4" />
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={() => {
                                setEditingId(pref.id);
                                setEditValue(pref.preference_value);
                              }}
                              className="p-1 text-gray-400 hover:text-blue-600"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(pref.id)}
                              className="p-1 text-gray-400 hover:text-red-500"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
