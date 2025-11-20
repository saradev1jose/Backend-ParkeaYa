import React, { useState, useEffect } from 'react';
import './OwnerProfile.css';
import API_BASE from '../../config';

const OwnerProfile = () => {
  const [ownerData, setOwnerData] = useState(null);
  const [parkingData, setParkingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('info');
  const [editing, setEditing] = useState(false);
  const [showParkingForm, setShowParkingForm] = useState(false);
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '', confirm_password: '' });
  const [changingPassword, setChangingPassword] = useState(false);
  const [formData, setFormData] = useState({});
  const [parkingForm, setParkingForm] = useState({
    nombre: '',
    direccion: '',
    coordenadas: '',
    telefono: '',
    descripcion: '',
    horario_apertura: '',
    horario_cierre: '',
    nivel_seguridad: 'Estándar',
    tarifa_hora: '',
    total_plazas: '',
    plazas_disponibles: '',
    servicios: [],
    imagenes: [],
    imagen_principal: null
  });

  const getAuthHeaders = (includeJson = true) => {
    const token = localStorage.getItem('access_token');
    const headers = {};
    if (includeJson) headers['Content-Type'] = 'application/json';
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
  };

  // Estado para ver/editar un estacionamiento
  const [selectedParking, setSelectedParking] = useState(null);
  const [showViewParking, setShowViewParking] = useState(false);
  const [showEditParking, setShowEditParking] = useState(false);
  const [editParkingForm, setEditParkingForm] = useState(null);

  // Cargar datos del owner
  const loadOwnerData = async () => {
    try {
      const response = await fetch(`${API_BASE}/users/profile/`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        console.log('📊 Datos del owner (raw):', data);

        const normalized = {

          ...data,

          first_name: data.first_name || data.nombre || data.name || (data.full_name ? data.full_name.split(' ')[0] : ''),
          last_name: data.last_name || data.apellido || (data.full_name ? data.full_name.split(' ').slice(1).join(' ') : ''),
          phone_number: data.phone_number || data.telefono || data.phone || '',
          address: data.address || data.direccion || data.address_line || '',
          is_active: (data.is_active !== undefined) ? data.is_active : (data.activo !== undefined ? data.activo : true),

          date_joined: data.date_joined || data.created_at || data.fecha_creacion || null
        };

        setOwnerData(normalized);
        setFormData({
          first_name: normalized.first_name || '',
          last_name: normalized.last_name || '',
          email: normalized.email || '',
          phone_number: normalized.phone_number || '',
          address: normalized.address || ''
        });
      } else {
        throw new Error('Error cargando datos del perfil');
      }
    } catch (error) {
      console.error('Error cargando datos del owner:', error);
      showNotification('Error cargando datos del perfil', 'error');
    }
  };

  // Cargar estacionamientos del owner
  const loadParkingData = async () => {
    try {
      const response = await fetch(`${API_BASE}/parking/my-parkings/`, {
        headers: getAuthHeaders()
      });

      console.log('🔄 Cargando estacionamientos...');
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Estacionamientos cargados:', data);
        setParkingData(data);

        // Si el perfil ya está cargado pero no tiene dirección, rellenarla desde el primer estacionamiento
        setOwnerData(prev => {
          try {
            if (!prev) return prev;
            if (prev.address && prev.address.trim() !== '') return prev;
            const first = Array.isArray(data) && data.length > 0 ? data[0] : null;
            const addr = first ? (first.direccion || first.address || first.location || '') : '';
            if (addr) {
              return { ...prev, address: addr };
            }
            return prev;
          } catch (err) {
            console.warn('No se pudo normalizar dirección desde estacionamientos:', err);
            return prev;
          }
        });
      } else if (response.status === 404) {
        console.log('ℹNo hay estacionamientos registrados');
        setParkingData([]);
      } else {
        throw new Error(`Error ${response.status} cargando estacionamientos`);
      }
    } catch (error) {
      console.error('Error cargando estacionamientos:', error);
      showNotification('Error cargando estacionamientos', 'error');
      setParkingData([]);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        await Promise.all([loadOwnerData(), loadParkingData()]);
      } catch (error) {
        console.error('Error en carga inicial:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Actualizar perfil del owner
  const updateOwnerProfile = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE}/users/owner/me/`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const updatedData = await response.json();
        setOwnerData(updatedData);
        setEditing(false);
        showNotification('Perfil actualizado correctamente', 'success');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al actualizar perfil');
      }
    } catch (error) {
      console.error('Error actualizando perfil:', error);
      showNotification(error.message, 'error');
    }
  };

  // Crear nuevo estacionamiento
  const createParking = async (e) => {
    e.preventDefault();
    try {
      // Preparar datos para la API

      // Usar FormData para permitir subir imágenes
      const formData = new FormData();
      formData.append('nombre', parkingForm.nombre);
      formData.append('direccion', parkingForm.direccion);
      formData.append('coordenadas', parkingForm.coordenadas || '');
      formData.append('telefono', parkingForm.telefono || '');
      formData.append('descripcion', parkingForm.descripcion || '');
      if (parkingForm.horario_apertura) formData.append('horario_apertura', parkingForm.horario_apertura);
      if (parkingForm.horario_cierre) formData.append('horario_cierre', parkingForm.horario_cierre);
      formData.append('nivel_seguridad', parkingForm.nivel_seguridad);
      formData.append('tarifa_hora', parkingForm.tarifa_hora);
      formData.append('total_plazas', parkingForm.total_plazas);
      formData.append('plazas_disponibles', parkingForm.plazas_disponibles);
      formData.append('servicios', JSON.stringify(parkingForm.servicios || []));
      formData.append('panel_local_id', `owner_${ownerData?.id}_${Date.now()}`);

      // Imagen principal (opcional)
      if (parkingForm.imagen_principal) {
        formData.append('imagen_principal', parkingForm.imagen_principal);
      }

      // Adjuntar imágenes (campo 'imagenes')
      if (parkingForm.imagenes && parkingForm.imagenes.length > 0) {
        parkingForm.imagenes.forEach((file, idx) => {
          formData.append('imagenes', file);
        });
      }

      console.log('📤 Enviando datos del estacionamiento (multipart):', parkingForm);

      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE}/parking/approval/requests/`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: formData
      });

      if (response.ok) {
        const newParking = await response.json();
        console.log('✅ Estacionamiento creado:', newParking);
        showNotification('Estacionamiento creado y enviado para aprobación', 'success');
        setShowParkingForm(false);
        resetParkingForm();
        // Recargar la lista de estacionamientos
        await loadParkingData();
      } else {
        const errorData = await response.json();
        console.error('❌ Error del servidor:', errorData);
        throw new Error(errorData.detail || errorData.message || 'Error creando estacionamiento');
      }
    } catch (error) {
      console.error('Error creando estacionamiento:', error);
      showNotification(error.message, 'error');
    }
  };

  // Ver detalles de un parking (trae detalle desde la API)
  const viewParkingDetails = async (id) => {
    try {
      console.log('🔍 Cargando detalle del parking ID:', id);

      const response = await fetch(`${API_BASE}/parking/${id}/`, { // ✅ URL corregida
        method: 'GET',
        headers: getAuthHeaders()
      });

      console.log('📡 Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Error response:', errorText);
        throw new Error(`Error ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log('✅ Detalle del parking cargado:', data);

      setSelectedParking(data);
      setShowViewParking(true);

    } catch (error) {
      console.error('❌ Error cargando detalle del parking:', error);
      showNotification(`No se pudo cargar el detalle: ${error.message}`, 'error');
    }
  };

  // Preparar formulario de edición - MEJORADO
  const openEditParking = async (parking) => {
    try {
      console.log('✏️ Preparando edición del parking:', parking.id);

      // Primero cargar los datos completos del parking
      const response = await fetch(`${API_BASE}/parking/${parking.id}/`, {
        headers: getAuthHeaders()
      });

      if (!response.ok) throw new Error('Error cargando datos para editar');

      const fullParkingData = await response.json();

      setEditParkingForm({
        id: fullParkingData.id,
        nombre: fullParkingData.nombre || '',
        direccion: fullParkingData.direccion || '',
        coordenadas: fullParkingData.coordenadas || '',
        telefono: fullParkingData.telefono || '',
        descripcion: fullParkingData.descripcion || '',
        horario_apertura: fullParkingData.horario_apertura || '',
        horario_cierre: fullParkingData.horario_cierre || '',
        nivel_seguridad: fullParkingData.nivel_seguridad || 'Estándar',
        tarifa_hora: fullParkingData.tarifa_hora || '',
        total_plazas: fullParkingData.total_plazas || '',
        plazas_disponibles: fullParkingData.plazas_disponibles || '',
        imagen_principal: fullParkingData.imagen_principal || null,
        servicios: fullParkingData.servicios || []
      });

      setShowEditParking(true);

    } catch (error) {
      console.error('❌ Error cargando datos para editar:', error);
      // Fallback: usar los datos básicos que ya tenemos
      setEditParkingForm({
        id: parking.id,
        nombre: parking.nombre || '',
        direccion: parking.direccion || '',
        coordenadas: parking.coordenadas || '',
        telefono: parking.telefono || '',
        descripcion: parking.descripcion || '',
        horario_apertura: parking.horario_apertura || '',
        horario_cierre: parking.horario_cierre || '',
        nivel_seguridad: parking.nivel_seguridad || 'Estándar',
        tarifa_hora: parking.tarifa_hora || '',
        total_plazas: parking.total_plazas || '',
        plazas_disponibles: parking.plazas_disponibles || '',
        imagen_principal: parking.imagen_principal || null,
        servicios: parking.servicios || []
      });
      setShowEditParking(true);
    }
  };

  // Enviar actualización del parking (PUT) - CORREGIDO
  const submitEditParking = async (e) => {
    e.preventDefault();
    try {
      if (!editParkingForm || !editParkingForm.id) {
        showNotification('No hay datos para actualizar', 'error');
        return;
      }

      console.log('📤 Enviando actualización del parking:', editParkingForm);

      const payload = { ...editParkingForm };
      delete payload.id;

      let response;
      const token = localStorage.getItem('access_token');

      // Si imagen_principal es un archivo, enviar multipart/form-data
      if (payload.imagen_principal && typeof payload.imagen_principal !== 'string') {
        const formData = new FormData();

        // Agregar todos los campos al FormData
        Object.keys(payload).forEach(key => {
          if (payload[key] !== null && payload[key] !== undefined) {
            if (key === 'servicios' && Array.isArray(payload[key])) {
              formData.append(key, JSON.stringify(payload[key]));
            } else if (key !== 'imagen_principal') {
              formData.append(key, payload[key]);
            }
          }
        });

        // Agregar la imagen principal si es un archivo nuevo
        formData.append('imagen_principal', payload.imagen_principal);

        response = await fetch(`${API_BASE}/parking/${editParkingForm.id}/`, { // ✅ URL corregida
          method: 'PUT',
          headers: token ? { 'Authorization': `Bearer ${token}` } : {},
          body: formData
        });
      } else {
        // Enviar como JSON normal
        response = await fetch(`${API_BASE}/parking/${editParkingForm.id}/`, { // ✅ URL corregida
          method: 'PUT',
          headers: getAuthHeaders(true),
          body: JSON.stringify(payload)
        });
      }

      console.log('📡 Response status:', response.status);

      if (response.ok) {
        const updatedData = await response.json();
        console.log('✅ Parking actualizado:', updatedData);

        showNotification('Estacionamiento actualizado correctamente', 'success');
        setShowEditParking(false);
        setEditParkingForm(null);

        // Recargar lista de estacionamientos
        await loadParkingData();
      } else {
        const errorData = await response.json().catch(() => null);
        console.error('❌ Error del servidor:', errorData);

        let errorMessage = 'Error actualizando estacionamiento';
        if (errorData) {
          if (errorData.detail) {
            errorMessage = errorData.detail;
          } else if (typeof errorData === 'object') {
            // Procesar errores de validación por campo
            const fieldErrors = [];
            Object.keys(errorData).forEach(field => {
              if (Array.isArray(errorData[field])) {
                fieldErrors.push(`${field}: ${errorData[field].join(', ')}`);
              } else {
                fieldErrors.push(`${field}: ${errorData[field]}`);
              }
            });
            if (fieldErrors.length > 0) {
              errorMessage = fieldErrors.join('; ');
            }
          }
        }

        throw new Error(errorMessage);
      }
    } catch (error) {
      console.error('❌ Error actualizando parking:', error);
      showNotification(error.message || 'Error actualizando estacionamiento', 'error');
    }
  };

  // También mejora el manejo de servicios en el formulario de edición
  const handleEditParkingChange = (e) => {
    const { name, value, type, checked, files } = e.target;

    if (type === 'checkbox') {
      setEditParkingForm(prev => ({
        ...prev,
        servicios: checked
          ? [...(prev.servicios || []), value]
          : (prev.servicios || []).filter(service => service !== value)
      }));
      return;
    }

    if (type === 'file') {
      const file = files && files[0] ? files[0] : null;
      setEditParkingForm(prev => ({ ...prev, [name]: file }));
      return;
    }

    setEditParkingForm(prev => ({ ...prev, [name]: value }));
  };

  // Resetear formulario de estacionamiento
  const resetParkingForm = () => {
    setParkingForm({
      nombre: '',
      direccion: '',
      coordenadas: '',
      telefono: '',
      descripcion: '',
      horario_apertura: '',
      horario_cierre: '',
      nivel_seguridad: 'Estándar',
      tarifa_hora: '',
      total_plazas: '',
      plazas_disponibles: '',
      servicios: [],
      imagenes: [],
      imagen_principal: null
    });
  };

  // Opciones predefinidas
  const securityLevels = ['Básico', 'Estándar', 'Premium', 'Alto'];
  const servicesOptions = [
    'Vigilancia 24/7',
    'Cámaras de seguridad',
    'Iluminación LED',
    'Cobertura techada',
    'Carga para EVs',
    'Lavado de autos',
    'Aceite y lubricación',
    'Asistencia mecánica',
    'Wi-Fi gratuito',
    'Cafetería'
  ];

  const handleParkingInputChange = (e) => {
    const { name, value, type, checked } = e.target;

    if (type === 'checkbox') {
      setParkingForm(prev => ({
        ...prev,
        servicios: checked
          ? [...prev.servicios, value]
          : prev.servicios.filter(service => service !== value)
      }));
      return;
    }

    if (type === 'file') {
      // Diferenciar entre imagen principal (single) y múltiples imágenes
      const files = Array.from(e.target.files || []);
      if (name === 'imagen_principal') {
        setParkingForm(prev => ({ ...prev, imagen_principal: files[0] || null }));
      } else {
        setParkingForm(prev => ({ ...prev, imagenes: files }));
      }
      return;
    } else {
      setParkingForm(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  // Formatear hora para mostrar
  const formatTimeForDisplay = (timeString) => {
    if (!timeString) return '24 horas';
    try {
      const [hours, minutes] = timeString.split(':');
      return `${hours}:${minutes}`;
    } catch (error) {
      return timeString;
    }
  };



  const showNotification = (message, type) => {
    // Usar el sistema de notificaciones existente del dashboard
    if (window.showDashboardNotification) {
      window.showDashboardNotification(message, type);
    } else {
      // Fallback simple
      const notification = document.createElement('div');
      notification.className = `dashboard-notification ${type}`;
      notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        background: ${type === 'success' ? '#10b981' : '#ef4444'};
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      `;
      notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check' : 'exclamation'}-circle"></i>
        <span style="margin-left: 8px;">${message}</span>
      `;
      document.body.appendChild(notification);

      setTimeout(() => {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 5000);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handlePasswordInputChange = (e) => {
    const { name, value } = e.target;
    setPasswordForm(prev => ({ ...prev, [name]: value }));
  };

  const submitChangePassword = async (e) => {
    e && e.preventDefault && e.preventDefault();
    if (changingPassword) return;

    const { old_password, new_password, confirm_password } = passwordForm;
    if (!old_password || !new_password) {
      showNotification('Completa las contraseñas requeridas', 'error');
      return;
    }
    if (new_password !== confirm_password) {
      showNotification('La nueva contraseña y la confirmación no coinciden', 'error');
      return;
    }
    if (new_password.length < 6) {
      showNotification('La nueva contraseña debe tener al menos 6 caracteres', 'error');
      return;
    }

    try {
      setChangingPassword(true);
      const response = await fetch(`${API_BASE}/users/profile/change-password/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ old_password, new_password, confirm_password })
      });

      const data = await response.json().catch(() => ({}));
      if (response.ok) {
        showNotification(data.message || 'Contraseña cambiada correctamente', 'success');
        setPasswordForm({ old_password: '', new_password: '', confirm_password: '' });
        setShowPasswordChange(false);
      } else {
        const err = data.error || data.detail || JSON.stringify(data) || 'Error cambiando contraseña';
        showNotification(err, 'error');
      }
    } catch (error) {
      console.error('Error cambiando contraseña:', error);
      showNotification('Error cambiando contraseña', 'error');
    } finally {
      setChangingPassword(false);
    }
  };

  if (loading) {
    return (
      <div className="profile-loading">
        <div className="loading-spinner"></div>
        <p>Cargando información del perfil...</p>
      </div>
    );
  }

  return (
    <div className="owner-profile">
      {/* Header del perfil */}
      <div className="profile-header">
        <div className="profile-avatar-section">
          <div className="avatar-container">
            <div className="avatar-placeholder">
              {ownerData?.first_name?.charAt(0) || ownerData?.phone_number?.slice(-2) || '?'}{ownerData?.last_name?.charAt(0) || ''}
            </div>
            <div className="online-indicator"></div>
          </div>
          <div className="profile-info">
            <h1>{ownerData?.first_name} {ownerData?.last_name}</h1>
            <p className="profile-role">
              <i className="fas fa-store"></i>
              Propietario de Estacionamiento
            </p>
            <p className="profile-email">
              <i className="fas fa-envelope"></i>
              {ownerData?.email}
            </p>
            <div className="profile-meta">
              <span className="meta-item">
                <i className="fas fa-calendar"></i>
                Registrado: {ownerData?.date_joined ? new Date(ownerData.date_joined).toLocaleDateString() : 'N/A'}
              </span>
              <span className={`status-badge ${ownerData?.is_active ? 'active' : 'inactive'}`}>
                <i className={`fas fa-${ownerData?.is_active ? 'check' : 'pause'}-circle`}></i>
                {ownerData?.is_active ? 'Activo' : 'Inactivo'}
              </span>
            </div>
          </div>
        </div>

        <div className="profile-stats-grid">
          <div className="stat-card primary">
            <div className="stat-icon">
              <i className="fas fa-parking"></i>
            </div>
            <div className="stat-content">
              <h3>{parkingData?.length || 0}</h3>
              <p>Estacionamientos</p>
            </div>
          </div>

          <div className="stat-card secondary">
            <div className="stat-icon">
              <i className="fas fa-phone"></i>
            </div>
            <div className="stat-content">
              <h3>{ownerData?.phone_number || 'No registrado'}</h3>
              <p>Teléfono</p>
            </div>
          </div>

          <div className="stat-card success">
            <div className="stat-icon">
              <i className="fas fa-check-circle"></i>
            </div>
            <div className="stat-content">
              <h3>{parkingData?.filter(p => p.aprobado).length || 0}</h3>
              <p>Aprobados</p>
            </div>
          </div>

          <div className="stat-card warning">
            <div className="stat-icon">
              <i className="fas fa-clock"></i>
            </div>
            <div className="stat-content">
              <h3>{parkingData?.filter(p => !p.aprobado).length || 0}</h3>
              <p>Pendientes</p>
            </div>
          </div>
        </div>
      </div>

      {/* Navegación por pestañas */}
      <div className="profile-tabs-container">
        <div className="profile-tabs">
          <button
            className={`tab-button ${activeTab === 'info' ? 'active' : ''}`}
            onClick={() => setActiveTab('info')}
          >
            <i className="fas fa-user"></i>
            Información Personal
          </button>
          <button
            className={`tab-button ${activeTab === 'parking' ? 'active' : ''}`}
            onClick={() => setActiveTab('parking')}
          >
            <i className="fas fa-parking"></i>
            Mis Estacionamientos
            {parkingData?.length > 0 && (
              <span className="tab-badge">{parkingData.length}</span>
            )}
          </button>
          <button
            className={`tab-button ${activeTab === 'security' ? 'active' : ''}`}
            onClick={() => setActiveTab('security')}
          >
            <i className="fas fa-shield-alt"></i>
            Seguridad
          </button>
        </div>
      </div>

      {/* Contenido de las pestañas */}
      <div className="tab-content-wrapper">
        {activeTab === 'info' && (
          <div className="info-tab">
            <div className="section-header">
              <div className="section-title">
                <i className="fas fa-user-circle"></i>
                <h2>Información Personal</h2>
              </div>
              <button
                className={`edit-btn ${editing ? 'cancel' : 'edit'}`}
                onClick={() => setEditing(!editing)}
              >
                <i className={`fas fa-${editing ? 'times' : 'edit'}`}></i>
                {editing ? 'Cancelar' : 'Editar Perfil'}
              </button>
            </div>

            {editing ? (
              <form onSubmit={updateOwnerProfile} className="profile-form">
                <div className="form-grid">
                  <div className="form-group">
                    <label>
                      <i className="fas fa-user"></i>
                      Nombre
                    </label>
                    <input
                      type="text"
                      name="first_name"
                      value={formData.first_name || ''}
                      onChange={handleInputChange}
                      required
                      placeholder="Ingresa tu nombre"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <i className="fas fa-user"></i>
                      Apellido
                    </label>
                    <input
                      type="text"
                      name="last_name"
                      value={formData.last_name || ''}
                      onChange={handleInputChange}
                      required
                      placeholder="Ingresa tu apellido"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <i className="fas fa-envelope"></i>
                      Email
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email || ''}
                      onChange={handleInputChange}
                      required
                      disabled
                      className="disabled-input"
                    />
                  </div>
                  <div className="form-group">
                    <label>
                      <i className="fas fa-phone"></i>
                      Teléfono
                    </label>
                    <input
                      type="tel"
                      name="phone_number"
                      value={formData.phone_number || ''}
                      onChange={handleInputChange}
                      placeholder="+51 987 654 321"
                    />
                  </div>
                  <div className="form-group full-width">
                    <label>
                      <i className="fas fa-map-marker-alt"></i>
                      Dirección
                    </label>
                    <input
                      type="text"
                      name="address"
                      value={formData.address || ''}
                      onChange={handleInputChange}
                      placeholder="Ingresa tu dirección completa"
                    />
                  </div>
                </div>
                <div className="form-actions">
                  <button type="submit" className="save-btn">
                    <i className="fas fa-save"></i>
                    Guardar Cambios
                  </button>
                </div>
              </form>
            ) : (
              <div className="info-display">
                <div className="info-grid">
                  <div className="info-card">
                    <div className="info-icon">
                      <i className="fas fa-id-card"></i>
                    </div>
                    <div className="info-content">
                      <label>Nombre Completo</label>
                      <p>{ownerData?.first_name} {ownerData?.last_name}</p>
                    </div>
                  </div>

                  <div className="info-card">
                    <div className="info-icon">
                      <i className="fas fa-envelope"></i>
                    </div>
                    <div className="info-content">
                      <label>Email</label>
                      <p>{ownerData?.email}</p>
                    </div>
                  </div>

                  <div className="info-card">
                    <div className="info-icon">
                      <i className="fas fa-phone"></i>
                    </div>
                    <div className="info-content">
                      <label>Teléfono</label>
                      <p>{ownerData?.phone_number || 'No registrado'}</p>
                    </div>
                  </div>

                  <div className="info-card">
                    <div className="info-icon">
                      <i className="fas fa-map-marker-alt"></i>
                    </div>
                    <div className="info-content">
                      <label>Dirección</label>
                      <p>{ownerData?.address || 'No registrada'}</p>
                    </div>
                  </div>

                  <div className="info-card">
                    <div className="info-icon">
                      <i className="fas fa-calendar-plus"></i>
                    </div>
                    <div className="info-content">
                      <label>Fecha de Registro</label>
                      <p>{ownerData?.date_joined ? new Date(ownerData.date_joined).toLocaleDateString('es-ES', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      }) : 'N/A'}</p>
                    </div>
                  </div>

                  <div className="info-card">
                    <div className="info-icon">
                      <i className="fas fa-user-shield"></i>
                    </div>
                    <div className="info-content">
                      <label>Estado de Cuenta</label>
                      <p className={`status ${ownerData?.is_active ? 'active' : 'inactive'}`}>
                        <i className={`fas fa-${ownerData?.is_active ? 'check' : 'pause'}-circle`}></i>
                        {ownerData?.is_active ? 'Activo' : 'Inactivo'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'parking' && (
          <div className="parking-tab">
            <div className="section-header">
              <div className="section-title">
                <i className="fas fa-parking"></i>
                <h2>Mis Estacionamientos</h2>
                {parkingData?.length > 0 && (
                  <span className="section-subtitle">
                    {parkingData.length} estacionamiento{parkingData.length !== 1 ? 's' : ''} registrado{parkingData.length !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
              <button
                className="add-parking-btn"
                onClick={() => setShowParkingForm(true)}
              >
                <i className="fas fa-plus"></i>
                Agregar Estacionamiento
              </button>
            </div>

            {showParkingForm && (
              <div className="parking-form-modal">
                <div className="modal-content">
                  <div className="modal-header">
                    <h3>
                      <i className="fas fa-plus-circle"></i>
                      Nuevo Estacionamiento
                    </h3>
                    <button
                      className="close-btn"
                      onClick={() => {
                        setShowParkingForm(false);
                        resetParkingForm();
                      }}
                    >
                      <i className="fas fa-times"></i>
                    </button>
                  </div>

                  <form onSubmit={createParking} className="parking-form">
                    <div className="form-columns">
                      <div className="form-column">
                        <h4>Información Básica</h4>

                        <div className="form-group">
                          <label>
                            <i className="fas fa-signature"></i>
                            Nombre del Estacionamiento *
                          </label>
                          <input
                            type="text"
                            name="nombre"
                            value={parkingForm.nombre}
                            onChange={handleParkingInputChange}
                            required
                            placeholder="Ej: Estacionamiento Central"
                          />
                        </div>

                        <div className="form-group">
                          <label>
                            <i className="fas fa-map-marker-alt"></i>
                            Dirección Completa *
                          </label>
                          <input
                            type="text"
                            name="direccion"
                            value={parkingForm.direccion}
                            onChange={handleParkingInputChange}
                            required
                            placeholder="Ej: Av. Principal #123, Ciudad"
                          />
                        </div>

                        <div className="form-group">
                          <label>
                            <i className="fas fa-map-pin"></i>
                            Coordenadas (Opcional)
                          </label>
                          <input
                            type="text"
                            name="coordenadas"
                            value={parkingForm.coordenadas}
                            onChange={handleParkingInputChange}
                            placeholder="Ej: 40.7128, -74.0060"
                          />
                        </div>

                        <div className="form-group">
                          <label>
                            <i className="fas fa-image"></i>
                            Imagen principal (opcional)
                          </label>
                          <input
                            type="file"
                            name="imagen_principal"
                            accept="image/*"
                            onChange={handleParkingInputChange}
                          />
                          <small className="form-help">Imagen principal mostrada en listados (JPG, PNG).</small>
                        </div>

                        <div className="form-group">
                          <label>
                            <i className="fas fa-images"></i>
                            Imágenes del estacionamiento (opcional)
                          </label>
                          <input
                            type="file"
                            name="imagenes"
                            accept="image/*"
                            multiple
                            onChange={handleParkingInputChange}
                          />
                          <small className="form-help">Puedes subir varias imágenes (JPG, PNG). Tamaño recomendado &lt; 5MB por imagen.</small>
                        </div>

                        <div className="form-group">
                          <label>
                            <i className="fas fa-phone"></i>
                            Teléfono de Contacto *
                          </label>
                          <input
                            type="tel"
                            name="telefono"
                            value={parkingForm.telefono}
                            onChange={handleParkingInputChange}
                            required
                            placeholder="+51 987 654 321"
                          />
                        </div>

                        <div className="form-group">
                          <label>
                            <i className="fas fa-align-left"></i>
                            Descripción
                          </label>
                          <textarea
                            name="descripcion"
                            value={parkingForm.descripcion}
                            onChange={handleParkingInputChange}
                            rows="3"
                            placeholder="Describe las características de tu estacionamiento..."
                          />
                        </div>
                      </div>

                      <div className="form-column">
                        <h4>Configuración Operativa</h4>

                        <div className="form-row">
                          <div className="form-group">
                            <label>
                              <i className="fas fa-clock"></i>
                              Horario Apertura
                            </label>
                            <input
                              type="time"
                              name="horario_apertura"
                              value={parkingForm.horario_apertura}
                              onChange={handleParkingInputChange}
                              placeholder="08:00"
                            />
                            <small className="form-help">Dejar vacío para 24 horas</small>
                          </div>

                          <div className="form-group">
                            <label>
                              <i className="fas fa-clock"></i>
                              Horario Cierre
                            </label>
                            <input
                              type="time"
                              name="horario_cierre"
                              value={parkingForm.horario_cierre}
                              onChange={handleParkingInputChange}
                              placeholder="22:00"
                            />
                            <small className="form-help">Dejar vacío para 24 horas</small>
                          </div>
                        </div>

                        <div className="form-group">
                          <label>
                            <i className="fas fa-shield-alt"></i>
                            Nivel de Seguridad *
                          </label>
                          <select
                            name="nivel_seguridad"
                            value={parkingForm.nivel_seguridad}
                            onChange={handleParkingInputChange}
                            required
                          >
                            {securityLevels.map(level => (
                              <option key={level} value={level}>
                                {level}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div className="form-group">
                          <label>
                            <i className="fas fa-money-bill-wave"></i>
                            Tarifa por Hora (S/) *
                          </label>
                          <input
                            type="number"
                            name="tarifa_hora"
                            value={parkingForm.tarifa_hora}
                            onChange={handleParkingInputChange}
                            required
                            min="0"
                            step="0.01"
                            placeholder="5.00"
                          />
                        </div>

                        <div className="form-row">
                          <div className="form-group">
                            <label>
                              <i className="fas fa-car"></i>
                              Total de Plazas *
                            </label>
                            <input
                              type="number"
                              name="total_plazas"
                              value={parkingForm.total_plazas}
                              onChange={handleParkingInputChange}
                              required
                              min="1"
                              placeholder="50"
                            />
                          </div>

                          <div className="form-group">
                            <label>
                              <i className="fas fa-car-side"></i>
                              Plazas Disponibles *
                            </label>
                            <input
                              type="number"
                              name="plazas_disponibles"
                              value={parkingForm.plazas_disponibles}
                              onChange={handleParkingInputChange}
                              required
                              min="0"
                              max={parkingForm.total_plazas || ''}
                              placeholder="45"
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="services-section">
                      <h4>
                        <i className="fas fa-concierge-bell"></i>
                        Servicios Adicionales
                      </h4>
                      <div className="services-grid">
                        {servicesOptions.map(service => (
                          <label key={service} className="service-checkbox">
                            <input
                              type="checkbox"
                              value={service}
                              checked={parkingForm.servicios.includes(service)}
                              onChange={handleParkingInputChange}
                            />
                            <span className="checkmark"></span>
                            {service}
                          </label>
                        ))}
                      </div>
                    </div>

                    <div className="form-actions">
                      <button
                        type="button"
                        className="cancel-btn"
                        onClick={() => {
                          setShowParkingForm(false);
                          resetParkingForm();
                        }}
                      >
                        <i className="fas fa-times"></i>
                        Cancelar
                      </button>
                      <button type="submit" className="submit-btn">
                        <i className="fas fa-plus-circle"></i>
                        Crear Estacionamiento
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {parkingData?.length > 0 ? (
              <div className="parking-grid">
                {parkingData.map(parking => (
                  <div key={parking.id} className="parking-card">
                    <div className="parking-header">
                      <div className="parking-title">
                        <h3>{parking.nombre}</h3>
                        <div className="parking-meta">
                          <span className={`status ${parking.aprobado ? 'approved' : 'pending'}`}>
                            <i className={`fas fa-${parking.aprobado ? 'check' : 'clock'}`}></i>
                            {parking.aprobado ? 'Aprobado' : 'Pendiente'}
                          </span>
                          <span className={`status ${parking.activo ? 'active' : 'inactive'}`}>
                            <i className={`fas fa-${parking.activo ? 'play' : 'pause'}`}></i>
                            {parking.activo ? 'Activo' : 'Inactivo'}
                          </span>
                        </div>
                      </div>
                      <div className="parking-rating">
                        <div className="stars">
                          {'★'.repeat(Math.round(parking.rating_promedio || 0))}
                          {'☆'.repeat(5 - Math.round(parking.rating_promedio || 0))}
                        </div>
                        <span>({parking.total_reseñas || 0})</span>
                      </div>
                    </div>

                    <div className="parking-info">
                      <div className="info-item">
                        <i className="fas fa-map-marker-alt"></i>
                        <span>{parking.direccion}</span>
                      </div>
                      <div className="info-item">
                        <i className="fas fa-car"></i>
                        <span>{parking.plazas_disponibles || 0}/{parking.total_plazas || 0} plazas disponibles</span>
                      </div>
                      <div className="info-item">
                        <i className="fas fa-money-bill-wave"></i>
                        <span>${parseFloat(parking.tarifa_hora || 0).toFixed(2)}/hora</span>
                      </div>
                      <div className="info-item">
                        <i className="fas fa-shield-alt"></i>
                        <span>Seguridad: {parking.nivel_seguridad || 'Estándar'}</span>
                      </div>
                      <div className="info-item">
                        <i className="fas fa-clock"></i>
                        <span>
                          Horario: {parking.horario_apertura ? formatTimeForDisplay(parking.horario_apertura) : '24'} -
                          {parking.horario_cierre ? formatTimeForDisplay(parking.horario_cierre) : '24'} horas
                        </span>
                      </div>
                    </div>

                    <div className="parking-actions">
                      <button className="action-btn edit" onClick={() => openEditParking(parking)}>
                        <i className="fas fa-edit"></i>
                        Editar
                      </button>
                      <button className="action-btn view" onClick={() => viewParkingDetails(parking.id)}>
                        <i className="fas fa-eye"></i>
                        Ver Detalles
                      </button>
                      <button className="action-btn stats">
                        <i className="fas fa-chart-bar"></i>
                        Estadísticas
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">🚗</div>
                <h3>No tienes estacionamientos registrados</h3>
                <p>Comienza agregando tu primer estacionamiento para gestionar tus espacios de parking</p>
                <button
                  className="add-parking-btn primary"
                  onClick={() => setShowParkingForm(true)}
                >
                  <i className="fas fa-plus"></i>
                  Agregar Primer Estacionamiento
                </button>
              </div>
            )}
            {/* Modal: Ver detalle de estacionamiento */}
            {showViewParking && selectedParking && (
              <div className="parking-view-modal">
                <div className="modal-content">
                  <div className="modal-header">
                    <h3>{selectedParking.nombre}</h3>
                    <button className="close-btn" onClick={() => setShowViewParking(false)}><i className="fas fa-times"></i></button>
                  </div>
                  <div className="modal-body">
                    {selectedParking.imagen_principal && (
                      <div className="parking-main-image">
                        <img src={selectedParking.imagen_principal} alt={selectedParking.nombre} style={{ maxWidth: '100%', borderRadius: 8 }} />
                      </div>
                    )}
                    {(!selectedParking.imagen_principal && selectedParking.imagenes && selectedParking.imagenes.length > 0) && (
                      <div className="parking-images-gallery">
                        {selectedParking.imagenes.map((img, idx) => (
                          <img key={idx} src={img.imagen || img.url || img} alt={`img-${idx}`} style={{ width: 120, marginRight: 8, borderRadius: 6 }} />
                        ))}
                      </div>
                    )}
                    <p><strong>Dirección:</strong> {selectedParking.direccion}</p>
                    <p><strong>Teléfono:</strong> {selectedParking.telefono}</p>
                    <p><strong>Tarifa/hora:</strong> S/ {parseFloat(selectedParking.tarifa_hora || 0).toFixed(2)}</p>
                    <p><strong>Plazas:</strong> {selectedParking.plazas_disponibles || 0}/{selectedParking.total_plazas || 0}</p>
                    <p><strong>Nivel seguridad:</strong> {selectedParking.nivel_seguridad}</p>
                    <p><strong>Descripción:</strong> {selectedParking.descripcion || '—'}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Modal: Editar estacionamiento */}
            {showEditParking && editParkingForm && (
              <div className="parking-edit-modal">
                <div className="modal-content">
                  <div className="modal-header">
                    <h3>Editar Estacionamiento</h3>
                    <button className="close-btn" onClick={() => { setShowEditParking(false); setEditParkingForm(null); }}><i className="fas fa-times"></i></button>
                  </div>
                  <form className="modal-body" onSubmit={submitEditParking}>
                    <div className="form-group">
                      <label>Nombre</label>
                      <input name="nombre" value={editParkingForm.nombre} onChange={handleEditParkingChange} required />
                    </div>
                    <div className="form-group">
                      <label>Dirección</label>
                      <input name="direccion" value={editParkingForm.direccion} onChange={handleEditParkingChange} required />
                    </div>
                    <div className="form-group">
                      <label>Coordenadas</label>
                      <input name="coordenadas" value={editParkingForm.coordenadas || ''} onChange={handleEditParkingChange} placeholder="lat, lon" />
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>Horario Apertura</label>
                        <input type="time" name="horario_apertura" value={editParkingForm.horario_apertura || ''} onChange={handleEditParkingChange} />
                      </div>
                      <div className="form-group">
                        <label>Horario Cierre</label>
                        <input type="time" name="horario_cierre" value={editParkingForm.horario_cierre || ''} onChange={handleEditParkingChange} />
                      </div>
                    </div>
                    <div className="form-group">
                      <label>Nivel de Seguridad</label>
                      <select name="nivel_seguridad" value={editParkingForm.nivel_seguridad || 'Estándar'} onChange={handleEditParkingChange}>
                        {securityLevels.map(level => (
                          <option key={level} value={level}>{level}</option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Imagen principal (opcional)</label>
                      <input type="file" name="imagen_principal" accept="image/*" onChange={handleEditParkingChange} />
                      {editParkingForm.imagen_principal && typeof editParkingForm.imagen_principal === 'string' && (
                        <div style={{ marginTop: 8 }}><img src={editParkingForm.imagen_principal} alt="preview" style={{ maxWidth: 160, borderRadius: 6 }} /></div>
                      )}
                    </div>
                    <div className="form-group">
                      <label>Teléfono</label>
                      <input name="telefono" value={editParkingForm.telefono} onChange={handleEditParkingChange} />
                    </div>
                    <div className="form-group">
                      <label>Tarifa / hora (S/)</label>
                      <input type="number" step="0.01" name="tarifa_hora" value={editParkingForm.tarifa_hora} onChange={handleEditParkingChange} />
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>Total Plazas</label>
                        <input type="number" name="total_plazas" value={editParkingForm.total_plazas} onChange={handleEditParkingChange} />
                      </div>
                      <div className="form-group">
                        <label>Plazas Disponibles</label>
                        <input type="number" name="plazas_disponibles" value={editParkingForm.plazas_disponibles} onChange={handleEditParkingChange} />
                      </div>
                    </div>
                    <div className="form-group">
                      <label>Descripción</label>
                      <textarea name="descripcion" value={editParkingForm.descripcion} onChange={handleEditParkingChange} rows="3" />
                    </div>
                    <div className="form-actions">
                      <button type="button" className="cancel-btn" onClick={() => { setShowEditParking(false); setEditParkingForm(null); }}>Cancelar</button>
                      <button type="submit" className="save-btn">Guardar</button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'security' && (
          <div className="security-tab">
            <div className="section-header">
              <div className="section-title">
                <i className="fas fa-shield-alt"></i>
                <h2>Seguridad y Cuenta</h2>
              </div>
            </div>

            <div className="security-sections">
              <div className="security-card">
                <div className="security-icon">
                  <i className="fas fa-key"></i>
                </div>
                <div className="security-content">
                  <h3>Cambiar Contraseña</h3>
                  <p>Actualiza tu contraseña regularmente para mantener tu cuenta segura</p>
                  {!showPasswordChange ? (
                    <button className="security-btn primary" onClick={() => setShowPasswordChange(true)}>
                      <i className="fas fa-sync-alt"></i>
                      Cambiar Contraseña
                    </button>
                  ) : (
                    <form className="password-change-form" onSubmit={submitChangePassword}>
                      <div className="form-group">
                        <label>Contraseña actual</label>
                        <input
                          type="password"
                          name="old_password"
                          value={passwordForm.old_password}
                          onChange={handlePasswordInputChange}
                          required
                        />
                      </div>
                      <div className="form-group">
                        <label>Nueva contraseña</label>
                        <input
                          type="password"
                          name="new_password"
                          value={passwordForm.new_password}
                          onChange={handlePasswordInputChange}
                          required
                        />
                      </div>
                      <div className="form-group">
                        <label>Confirmar nueva contraseña</label>
                        <input
                          type="password"
                          name="confirm_password"
                          value={passwordForm.confirm_password}
                          onChange={handlePasswordInputChange}
                          required
                        />
                      </div>
                      <div className="form-actions">
                        <button type="button" className="cancel-btn" onClick={() => setShowPasswordChange(false)}>Cancelar</button>
                        <button type="submit" className="save-btn" disabled={changingPassword}>{changingPassword ? 'Guardando...' : 'Guardar'}</button>
                      </div>
                    </form>
                  )}
                </div>
              </div>

              <div className="security-card">
                <div className="security-icon">
                  <i className="fas fa-desktop"></i>
                </div>
                <div className="security-content">
                  <h3>Sesión Actual</h3>
                  <p>Gestiona tu sesión actual y dispositivos conectados</p>
                  <button className="security-btn secondary">
                    <i className="fas fa-cog"></i>
                    Gestionar Sesión
                  </button>
                </div>
              </div>

              <div className="security-card warning">
                <div className="security-icon">
                  <i className="fas fa-exclamation-triangle"></i>
                </div>
                <div className="security-content">
                  <h3>Zona de Peligro</h3>
                  <p>Acciones que no se pueden deshacer. Procede con precaución.</p>
                  <button className="security-btn danger">
                    <i className="fas fa-user-slash"></i>
                    Desactivar Cuenta
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OwnerProfile;