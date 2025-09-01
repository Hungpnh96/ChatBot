import React, { useState, useEffect } from 'react';
import { healthCheck, getProviderInfo } from '../api.ts';

// Get API base URL based on current hostname
const getApiBaseUrl = () => {
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8000';
  }
  return 'https://chat.hungpnh.dev';
};

interface SystemStatus {
  status: string;
  timestamp: string;
  services: {
    database: boolean;
    ai: boolean;
    voice: boolean;
  };
  message: string;
}

interface ModelInfo {
  total_models: number;
  available_models: number;
  required_models: number;
  missing_required: number;
  models_by_type: {
    ollama: Array<{
      name: string;
      status: string;
      size_mb: number;
      required: boolean;
    }>;
    vosk: Array<{
      name: string;
      status: string;
      size_mb: number;
      required: boolean;
    }>;
  };
}

interface OllamaStatus {
  models: Array<{
    name: string;
    size: string;
    modified: string;
  }>;
  server_status: 'running' | 'stopped' | 'error';
}

const HealthDashboard: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchSystemStatus = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch system health
      const health = await healthCheck();
      // Map API response to our interface
      const mappedHealth: SystemStatus = {
        status: health.status,
        timestamp: new Date().toISOString(),
        services: {
          database: health.data?.ai_available || false, // Assuming database is available if AI is available
          ai: health.data?.ai_available || false,
          voice: health.voice_health?.speech_recognition_available || false
        },
        message: health.message || 'System status unknown'
      };
      setSystemStatus(mappedHealth);

      // Fetch models status
      try {
        const modelsResponse = await fetch(`${getApiBaseUrl()}/api/models/status`);
        if (modelsResponse.ok) {
          const modelsData = await modelsResponse.json();
          setModelInfo(modelsData.data);
        }
      } catch (e) {
        console.warn('Models status fetch failed:', e);
      }

      // Fetch Ollama status
      try {
        const ollamaResponse = await fetch(`${getApiBaseUrl()}/api/ollama/status`);
        if (ollamaResponse.ok) {
          const ollamaData = await ollamaResponse.json();
          setOllamaStatus(ollamaData);
        }
      } catch (e) {
        console.warn('Ollama status fetch failed:', e);
      }

      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemStatus();
  }, []);

  const getStatusColor = (status: boolean | string) => {
    if (typeof status === 'boolean') {
      return status ? '#10b981' : '#ef4444';
    }
    switch (status) {
      case 'available':
      case 'running':
        return '#10b981';
      case 'not_found':
      case 'stopped':
        return '#f59e0b';
      case 'error':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const getStatusIcon = (status: boolean | string) => {
    if (typeof status === 'boolean') {
      return status ? '✅' : '❌';
    }
    switch (status) {
      case 'available':
      case 'running':
        return '✅';
      case 'not_found':
      case 'stopped':
        return '⚠️';
      case 'error':
        return '❌';
      default:
        return '❓';
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatSizeMB = (mb: number) => {
    return formatBytes(mb * 1024 * 1024);
  };

  if (loading && !systemStatus) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '18px',
        color: '#6b7280'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
          <div>Đang kiểm tra hệ thống...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f8fafc',
      padding: '24px',
      fontFamily: "'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif"
    }}>
      {/* Header */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: '16px',
        padding: '24px',
        marginBottom: '24px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        border: '1px solid #e5e7eb'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px'
        }}>
          <div>
            <h1 style={{
              margin: 0,
              fontSize: '28px',
              fontWeight: '700',
              color: '#111827'
            }}>
              🏥 Health Dashboard
            </h1>
            <p style={{
              margin: '8px 0 0 0',
              color: '#6b7280',
              fontSize: '16px'
            }}>
              Trang quản lý trạng thái hệ thống ChatBot
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            {lastUpdate && (
              <div style={{
                fontSize: '14px',
                color: '#6b7280',
                textAlign: 'right'
              }}>
                <div>Cập nhật lần cuối:</div>
                <div style={{ fontWeight: '500' }}>
                  {lastUpdate.toLocaleString('vi-VN')}
                </div>
              </div>
            )}
            <button
              onClick={fetchSystemStatus}
              disabled={loading}
              style={{
                padding: '12px 24px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.6 : 1,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                if (!loading) e.currentTarget.style.backgroundColor = '#2563eb';
              }}
              onMouseLeave={(e) => {
                if (!loading) e.currentTarget.style.backgroundColor = '#3b82f6';
              }}
            >
              {loading ? '🔄' : '🔄'} Reload
            </button>
          </div>
        </div>

        {error && (
          <div style={{
            padding: '16px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            color: '#dc2626',
            marginBottom: '16px'
          }}>
            <strong>Lỗi:</strong> {error}
          </div>
        )}

        {/* Overall Status */}
        {systemStatus && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px'
          }}>
            <div style={{
              padding: '20px',
              backgroundColor: '#f0fdf4',
              border: '1px solid #bbf7d0',
              borderRadius: '12px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>
                {getStatusIcon(systemStatus.services.database)}
              </div>
              <div style={{ fontWeight: '600', color: '#166534' }}>Database</div>
              <div style={{ fontSize: '14px', color: '#16a34a' }}>
                {systemStatus.services.database ? 'Sẵn sàng' : 'Không sẵn sàng'}
              </div>
            </div>

            <div style={{
              padding: '20px',
              backgroundColor: '#f0f9ff',
              border: '1px solid #bae6fd',
              borderRadius: '12px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>
                {getStatusIcon(systemStatus.services.ai)}
              </div>
              <div style={{ fontWeight: '600', color: '#1e40af' }}>AI Service</div>
              <div style={{ fontSize: '14px', color: '#0284c7' }}>
                {systemStatus.services.ai ? 'Sẵn sàng' : 'Không sẵn sàng'}
              </div>
            </div>

            <div style={{
              padding: '20px',
              backgroundColor: '#fef3c7',
              border: '1px solid #fde68a',
              borderRadius: '12px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>
                {getStatusIcon(systemStatus.services.voice)}
              </div>
              <div style={{ fontWeight: '600', color: '#92400e' }}>Voice Service</div>
              <div style={{ fontSize: '14px', color: '#d97706' }}>
                {systemStatus.services.voice ? 'Sẵn sàng' : 'Không sẵn sàng'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Models Status */}
      {modelInfo && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          padding: '24px',
          marginBottom: '24px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          border: '1px solid #e5e7eb'
        }}>
          <h2 style={{
            margin: '0 0 20px 0',
            fontSize: '24px',
            fontWeight: '600',
            color: '#111827'
          }}>
            🤖 AI Models Status
          </h2>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '16px',
            marginBottom: '24px'
          }}>
            <div style={{
              padding: '16px',
              backgroundColor: '#f8fafc',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#3b82f6' }}>
                {modelInfo.total_models}
              </div>
              <div style={{ fontSize: '14px', color: '#6b7280' }}>Tổng Models</div>
            </div>
            <div style={{
              padding: '16px',
              backgroundColor: '#f0fdf4',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#10b981' }}>
                {modelInfo.available_models}
              </div>
              <div style={{ fontSize: '14px', color: '#6b7280' }}>Available</div>
            </div>
            <div style={{
              padding: '16px',
              backgroundColor: '#fef3c7',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#f59e0b' }}>
                {modelInfo.missing_required}
              </div>
              <div style={{ fontSize: '14px', color: '#6b7280' }}>Missing Required</div>
            </div>
          </div>

          {/* Ollama Models */}
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{
              margin: '0 0 16px 0',
              fontSize: '20px',
              fontWeight: '600',
              color: '#374151'
            }}>
              🦙 Ollama Models
            </h3>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '16px'
            }}>
              {modelInfo.models_by_type.ollama.map((model, index) => (
                <div
                  key={index}
                  style={{
                    padding: '16px',
                    backgroundColor: '#f8fafc',
                    border: `2px solid ${getStatusColor(model.status)}`,
                    borderRadius: '12px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div>
                    <div style={{ fontWeight: '600', color: '#111827', marginBottom: '4px' }}>
                      {model.name}
                    </div>
                    <div style={{ fontSize: '14px', color: '#6b7280' }}>
                      Size: {formatSizeMB(model.size_mb)}
                    </div>
                  </div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    <span style={{ fontSize: '20px' }}>
                      {getStatusIcon(model.status)}
                    </span>
                    <span style={{
                      fontSize: '14px',
                      fontWeight: '500',
                      color: getStatusColor(model.status)
                    }}>
                      {model.status === 'available' ? 'Available' : 'Not Found'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Vosk Models */}
          <div>
            <h3 style={{
              margin: '0 0 16px 0',
              fontSize: '20px',
              fontWeight: '600',
              color: '#374151'
            }}>
              🎤 Vosk Models (Voice Recognition)
            </h3>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '16px'
            }}>
              {modelInfo.models_by_type.vosk.map((model, index) => (
                <div
                  key={index}
                  style={{
                    padding: '16px',
                    backgroundColor: '#f8fafc',
                    border: `2px solid ${getStatusColor(model.status)}`,
                    borderRadius: '12px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div>
                    <div style={{ fontWeight: '600', color: '#111827', marginBottom: '4px' }}>
                      {model.name}
                    </div>
                    <div style={{ fontSize: '14px', color: '#6b7280' }}>
                      Size: {formatSizeMB(model.size_mb)}
                      {model.required && (
                        <span style={{
                          backgroundColor: '#ef4444',
                          color: 'white',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          marginLeft: '8px'
                        }}>
                          Required
                        </span>
                      )}
                    </div>
                  </div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    <span style={{ fontSize: '20px' }}>
                      {getStatusIcon(model.status)}
                    </span>
                    <span style={{
                      fontSize: '14px',
                      fontWeight: '500',
                      color: getStatusColor(model.status)
                    }}>
                      {model.status === 'available' ? 'Available' : 'Not Found'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Ollama Service Status */}
      {ollamaStatus && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          padding: '24px',
          marginBottom: '24px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          border: '1px solid #e5e7eb'
        }}>
          <h2 style={{
            margin: '0 0 20px 0',
            fontSize: '24px',
            fontWeight: '600',
            color: '#111827'
          }}>
            🦙 Ollama Service Status
          </h2>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            marginBottom: '24px'
          }}>
            <div style={{
              padding: '12px 20px',
              backgroundColor: getStatusColor(ollamaStatus.server_status) === '#10b981' ? '#f0fdf4' : '#fef2f2',
              border: `2px solid ${getStatusColor(ollamaStatus.server_status)}`,
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span style={{ fontSize: '24px' }}>
                {getStatusIcon(ollamaStatus.server_status)}
              </span>
              <span style={{
                fontWeight: '600',
                color: getStatusColor(ollamaStatus.server_status)
              }}>
                Server: {ollamaStatus.server_status === 'running' ? 'Running' : 'Stopped'}
              </span>
            </div>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '16px'
          }}>
            {ollamaStatus.models.map((model, index) => (
              <div
                key={index}
                style={{
                  padding: '16px',
                  backgroundColor: '#f8fafc',
                  border: '1px solid #e5e7eb',
                  borderRadius: '12px'
                }}
              >
                <div style={{ fontWeight: '600', color: '#111827', marginBottom: '8px' }}>
                  {model.name}
                </div>
                <div style={{ fontSize: '14px', color: '#6b7280' }}>
                  Size: {model.size}
                </div>
                <div style={{ fontSize: '14px', color: '#6b7280' }}>
                  Modified: {new Date(model.modified).toLocaleString('vi-VN')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* System Info */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: '16px',
        padding: '24px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        border: '1px solid #e5e7eb'
      }}>
        <h2 style={{
          margin: '0 0 20px 0',
          fontSize: '24px',
          fontWeight: '600',
          color: '#111827'
        }}>
          ℹ️ System Information
        </h2>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '16px'
        }}>
          <div style={{
            padding: '16px',
            backgroundColor: '#f8fafc',
            borderRadius: '8px'
          }}>
            <div style={{ fontWeight: '600', color: '#374151', marginBottom: '4px' }}>
              Environment
            </div>
            <div style={{ color: '#6b7280' }}>
              {window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'Development (Local)' : 'Production'}
            </div>
          </div>

          <div style={{
            padding: '16px',
            backgroundColor: '#f8fafc',
            borderRadius: '8px'
          }}>
            <div style={{ fontWeight: '600', color: '#374151', marginBottom: '4px' }}>
              API Base URL
            </div>
            <div style={{ color: '#6b7280' }}>
              {window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'http://localhost:8000' : 'https://chat.hungpnh.dev'}
            </div>
          </div>

          <div style={{
            padding: '16px',
            backgroundColor: '#f8fafc',
            borderRadius: '8px'
          }}>
            <div style={{ fontWeight: '600', color: '#374151', marginBottom: '4px' }}>
              Backend Port
            </div>
            <div style={{ color: '#6b7280' }}>8000</div>
          </div>

          <div style={{
            padding: '16px',
            backgroundColor: '#f8fafc',
            borderRadius: '8px'
          }}>
            <div style={{ fontWeight: '600', color: '#374151', marginBottom: '4px' }}>
              Frontend Port
            </div>
            <div style={{ color: '#6b7280' }}>3000</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HealthDashboard;
