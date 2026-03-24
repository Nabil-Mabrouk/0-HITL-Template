import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ServiceCard } from './ServiceCard';
import { RecentServices } from './RecentServices';
import { UsageStats } from './UsageStats';
import { Loader2, Plus, Search, Filter } from 'lucide-react';

// Types
interface Service {
  slug: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  agents_count: number;
  workflows_count: number;
}

export default function DashboardLayout() {
  const { user, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [services, setServices] = useState<Service[]>([]);
  const [filteredServices, setFilteredServices] = useState<Service[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Fetch available services
  useEffect(() => {
    fetchServices();
  }, []);

  // Filter services based on search and category
  useEffect(() => {
    let filtered = services;

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        service =>
          service.name.toLowerCase().includes(query) ||
          service.description.toLowerCase().includes(query) ||
          service.category.toLowerCase().includes(query)
      );
    }

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(service => service.category === selectedCategory);
    }

    setFilteredServices(filtered);
  }, [services, searchQuery, selectedCategory]);

  const fetchServices = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/agent-services/services');
      if (response.ok) {
        const data = await response.json();
        setServices(data);
        setFilteredServices(data);
      } else {
        console.error('Failed to fetch services');
      }
    } catch (error) {
      console.error('Error fetching services:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Extract unique categories
  const categories = ['all', ...new Set(services.map(service => service.category))];

  // Get icon component based on icon name
  const getIcon = (iconName: string) => {
    // This is a simplified version - in a real app, you'd have a proper icon mapping
    const iconMap: Record<string, string> = {
      newspaper: '📰',
      'book-open': '📚',
      bitcoin: '₿',
      activity: '⚡',
      settings: '⚙️',
    };
    return iconMap[iconName] || '🔧';
  };

  const handleServiceClick = (serviceSlug: string) => {
    navigate(`/dashboard/${serviceSlug}`);
  };

  const handleAddService = () => {
    // Navigate to service creation page (admin only)
    navigate('/admin/agent-services/new');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 animate-spin text-blue-500" />
          <p className="text-gray-600">Chargement des services...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="container mx-auto px-6 py-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Agentic AI Services</h1>
              <p className="text-gray-600 mt-2">
                Sélectionnez un service pour commencer à travailler avec nos agents IA
              </p>
            </div>

            <div className="flex items-center gap-4">
              {/* Search bar */}
              <div className="relative flex-1 md:flex-none">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Rechercher un service..."
                  className="pl-10 pr-4 py-2 border rounded-lg w-full md:w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              {/* Category filter */}
              <div className="flex items-center gap-2">
                <Filter className="w-5 h-5 text-gray-400" />
                <select
                  className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                >
                  {categories.map(category => (
                    <option key={category} value={category}>
                      {category === 'all' ? 'Toutes les catégories' : category}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Stats Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg p-6 shadow">
            <h3 className="text-lg font-semibold text-gray-900">Services disponibles</h3>
            <p className="text-3xl font-bold mt-2">{services.length}</p>
            <p className="text-gray-600 text-sm mt-1">Services actifs</p>
          </div>
          <div className="bg-white rounded-lg p-6 shadow">
            <h3 className="text-lg font-semibold text-gray-900">Agents déployés</h3>
            <p className="text-3xl font-bold mt-2">
              {services.reduce((sum, service) => sum + service.agents_count, 0)}
            </p>
            <p className="text-gray-600 text-sm mt-1">Agents en fonctionnement</p>
          </div>
          <div className="bg-white rounded-lg p-6 shadow">
            <h3 className="text-lg font-semibold text-gray-900">Workflows</h3>
            <p className="text-3xl font-bold mt-2">
              {services.reduce((sum, service) => sum + service.workflows_count, 0)}
            </p>
            <p className="text-gray-600 text-sm mt-1">Workflows prédéfinis</p>
          </div>
        </div>

        {/* Services Grid */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              Services disponibles ({filteredServices.length})
            </h2>
            {isAdmin && (
              <button
                onClick={handleAddService}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-5 h-5" />
                Ajouter un service
              </button>
            )}
          </div>

          {filteredServices.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <p className="text-gray-600">Aucun service trouvé</p>
              <p className="text-gray-500 text-sm mt-2">
                Essayez de modifier vos critères de recherche
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredServices.map(service => (
                <ServiceCard
                  key={service.slug}
                  service={{
                    ...service,
                    icon: getIcon(service.icon)
                  }}
                  onClick={() => handleServiceClick(service.slug)}
                />
              ))}

              {/* Add Service Card (Admin only) */}
              {isAdmin && (
                <div
                  onClick={handleAddService}
                  className="border-2 border-dashed border-gray-300 rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer hover:border-blue-500 transition-colors bg-white"
                >
                  <div className="w-12 h-12 flex items-center justify-center rounded-full bg-blue-50 text-blue-600 mb-4">
                    <Plus className="w-6 h-6" />
                  </div>
                  <h3 className="font-medium text-gray-900">Ajouter un service</h3>
                  <p className="text-sm text-gray-500 text-center mt-1">
                    Configurez un nouveau service agentic IA
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Recent Services & Usage Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <RecentServices />
          <UsageStats />
        </div>

        {/* Quick Actions */}
        <div className="mt-12 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Actions rapides</h2>
          <div className="flex flex-wrap gap-4">
            <button
              onClick={() => navigate('/dashboard/executions')}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Voir mon historique
            </button>
            <button
              onClick={() => navigate('/dashboard/favorites')}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Mes favoris
            </button>
            <button
              onClick={() => navigate('/dashboard/settings')}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Paramètres
            </button>
            <button
              onClick={fetchServices}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Actualiser
            </button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t bg-white mt-12">
        <div className="container mx-auto px-6 py-6">
          <p className="text-gray-600 text-sm text-center">
            © {new Date().getFullYear()} {{PROJECT_NAME}}. Tous droits réservés.
          </p>
          <p className="text-gray-500 text-xs text-center mt-2">
            Système agentic IA • Version 1.0.0
          </p>
        </div>
      </footer>
    </div>
  );
}