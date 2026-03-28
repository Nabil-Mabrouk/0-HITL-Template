
interface ServiceCardProps {
  service: {
    slug: string;
    name: string;
    description: string;
    icon: string;
    category: string;
    agents_count: number;
    workflows_count: number;
  };
  onClick: () => void;
}

export function ServiceCard({ service, onClick }: ServiceCardProps) {
  // Map category to color
  const categoryColors: Record<string, string> = {
    content: 'bg-blue-100 text-blue-800',
    academic: 'bg-green-100 text-green-800',
    finance: 'bg-purple-100 text-purple-800',
    general: 'bg-gray-100 text-gray-800',
    development: 'bg-yellow-100 text-yellow-800',
  };

  const categoryColor = categoryColors[service.category] || 'bg-gray-100 text-gray-800';

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer border border-gray-200 overflow-hidden"
    >
      {/* Service Header */}
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 flex items-center justify-center rounded-lg bg-gray-50 text-2xl">
              {service.icon}
            </div>
            <div>
              <h3 className="font-bold text-lg text-gray-900">{service.name}</h3>
              <span className={`text-xs px-2 py-1 rounded-full ${categoryColor} font-medium`}>
                {service.category}
              </span>
            </div>
          </div>

          {/* Quick actions menu (simplified for now) */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              // Handle quick action (e.g., favorite, settings)
            }}
            className="text-gray-400 hover:text-gray-600"
          >
            ⋮
          </button>
        </div>

        {/* Service Description */}
        <p className="text-gray-600 mt-4 line-clamp-2">{service.description}</p>

        {/* Service Stats */}
        <div className="flex items-center gap-6 mt-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-blue-500"></div>
            <span className="text-gray-700">
              {service.agents_count} agent{service.agents_count !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="text-gray-700">
              {service.workflows_count} workflow{service.workflows_count !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      </div>

      {/* Service Footer */}
      <div className="border-t px-6 py-4 bg-gray-50">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">Cliquez pour ouvrir</span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onClick();
            }}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
          >
            Utiliser
          </button>
        </div>
      </div>
    </div>
  );
}