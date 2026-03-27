interface Props {
  platform: string | null;
  format: string | null;
  configType: string | null;
  confidence: number | null;
  method?: string;
}

const platformLabels: Record<string, string> = {
  teamcity: "TeamCity",
  jenkins: "Jenkins",
};

const formatLabels: Record<string, string> = {
  kotlin_dsl: "Kotlin DSL",
  xml: "XML",
  json_api: "JSON API",
  groovy: "Groovy",
};

const configTypeLabels: Record<string, string> = {
  shared_library: "Shared Library",
  complete_pipeline: "Complete Pipeline",
  fragment: "Fragment",
};

export function DetectionBadge({ platform, format, configType, confidence, method }: Props) {
  if (!platform) return null;

  const confidenceColor =
    (confidence || 0) >= 0.8
      ? "text-green-700 bg-green-50 border-green-200"
      : (confidence || 0) >= 0.5
        ? "text-yellow-700 bg-yellow-50 border-yellow-200"
        : "text-red-700 bg-red-50 border-red-200";

  return (
    <div className="flex flex-wrap gap-2">
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
        {platformLabels[platform] || platform}
      </span>
      {format && (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200">
          {formatLabels[format] || format}
        </span>
      )}
      {configType && (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-50 text-gray-700 border border-gray-200">
          {configTypeLabels[configType] || configType}
        </span>
      )}
      {confidence !== null && (
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${confidenceColor}`}
        >
          {Math.round(confidence * 100)}% confidence
          {method && ` (${method})`}
        </span>
      )}
    </div>
  );
}
