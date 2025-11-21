package com.example.smarparkinapp.ui.theme.screens.profile

import android.content.Context
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.smarparkinapp.R
import com.example.smarparkinapp.ui.theme.viewmodel.ProfileViewModel
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.CardDefaults
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.IconButton
import androidx.compose.material3.Icon
import androidx.compose.ui.draw.clip

@Composable
fun ErrorCard(
    message: String,
    onRetry: (() -> Unit)?,
    onDismiss: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = message,
                modifier = Modifier.weight(1f),
                color = MaterialTheme.colorScheme.onErrorContainer
            )
            IconButton(onClick = onDismiss) {
                Icon(Icons.Default.Close, contentDescription = "Cerrar")
            }
        }
    }
}

@Composable
fun SuccessCard(
    message: String,
    onDismiss: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = message,
                modifier = Modifier.weight(1f),
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
            IconButton(onClick = onDismiss) {
                Icon(Icons.Default.Close, contentDescription = "Cerrar")
            }
        }
    }
}

@Composable
fun ProfilePhotoSection() {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Box(
            modifier = Modifier
                .size(120.dp)
                .background(
                    color = MaterialTheme.colorScheme.surfaceVariant,
                    shape = CircleShape
                ),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = Icons.Default.Edit,
                contentDescription = "Foto de perfil",
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.size(40.dp)
            )
        }
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Cambiar foto",
            color = MaterialTheme.colorScheme.primary,
            fontWeight = FontWeight.Medium
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileScreen(
    onBackClick: () -> Unit,
    viewModel: ProfileViewModel = viewModel()
) {
    val context = LocalContext.current

    // Cargar perfil al iniciar la pantalla
    LaunchedEffect(Unit) {
        viewModel.loadUserProfile(context)
    }

    ProfileScreenContent(
        viewModel = viewModel,
        onBackClick = onBackClick,
        context = context
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileScreenContent(
    viewModel: ProfileViewModel,
    onBackClick: () -> Unit,
    context: Context
) {
    val userProfile by viewModel.userProfile.collectAsState(initial = null)
    val isLoading by viewModel.isLoading.collectAsState()
    val errorMessage by viewModel.errorMessage.collectAsState()
    val updateSuccess by viewModel.updateSuccess.collectAsState()
    val validationErrors by viewModel.validationErrors.collectAsState()

    // Observa el flag de éxito y navega cuando la actualización termine
    LaunchedEffect(updateSuccess) {
        if (updateSuccess == true) {
            onBackClick()
            viewModel.resetUpdateSuccess()
        }
    }

    // Estados locales
    var firstName by remember { mutableStateOf("") }
    var lastName by remember { mutableStateOf("") }
    var documentType by remember { mutableStateOf("") }
    var documentNumber by remember { mutableStateOf("") }
    var birthDate by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("") }
    var postalCode by remember { mutableStateOf("") }
    var country by remember { mutableStateOf("Perú") }
    var address by remember { mutableStateOf("") }

    // Estado para formato de documento
    var documentHint by remember { mutableStateOf("Ej: 87654321") }

    // Actualizar hint según tipo de documento
    LaunchedEffect(documentType) {
        documentHint = when (documentType) {
            "DNI" -> "8 dígitos (Ej: 87654321)"
            "Pasaporte" -> "6-12 caracteres (Ej: AB123456)"
            "Carnet de Extranjería" -> "9-12 caracteres (Ej: A123456789)"
            else -> "Ingrese número"
        }

        // Limpiar número cuando cambia el tipo
        documentNumber = ""
    }

    // Cargar datos del perfil en los estados locales
    LaunchedEffect(userProfile) {
        userProfile?.let { profile ->
            firstName = profile.firstName ?: ""
            lastName = profile.lastName ?: ""
            phone = profile.phone ?: ""
            address = profile.address ?: ""
            documentType = when (profile.tipoDocumento) {
                "dni" -> "DNI"
                "pasaporte" -> "Pasaporte"
                "carnet_extranjeria" -> "Carnet de Extranjería"
                else -> profile.tipoDocumento ?: ""
            }
            documentNumber = profile.numeroDocumento ?: ""
            birthDate = profile.fechaNacimiento ?: ""
            postalCode = profile.codigoPostal ?: ""
            country = profile.pais ?: "Perú"
        }
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("Actualizar Datos") },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Volver")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            // Mensajes de error general
            errorMessage?.let { message ->
                ErrorCard(
                    message = message,
                    onRetry = null,
                    onDismiss = { viewModel.clearError() }
                )
            }

            // Mensajes de éxito
            if (updateSuccess == true) {
                SuccessCard(
                    message = "Perfil actualizado correctamente",
                    onDismiss = { viewModel.resetUpdateSuccess() }
                )
            }

            // Formulario
            ProfileForm(
                firstName = firstName,
                lastName = lastName,
                documentType = documentType,
                documentNumber = documentNumber,
                documentHint = documentHint,
                birthDate = birthDate,
                phone = phone,
                postalCode = postalCode,
                country = country,
                address = address,
                validationErrors = validationErrors ?: emptyMap(),
                onFirstNameChange = { firstName = it },
                onLastNameChange = { lastName = it },
                onDocumentTypeChange = {
                    documentType = it
                    viewModel.clearValidationErrors()
                },
                onDocumentNumberChange = {
                    documentNumber = it
                    if (validationErrors?.containsKey("documentNumber") == true) {
                        viewModel.clearValidationErrors()
                    }
                },
                onBirthDateChange = { birthDate = it },
                onPhoneChange = { phone = it },
                onPostalCodeChange = { postalCode = it },
                onCountryChange = { country = it },
                onAddressChange = { address = it },
                isLoading = isLoading,
                onSaveClick = {
                    // Antes de enviar, mapear el tipo de documento al formato backend
                    val backendDocumentType = mapDocumentTypeToBackendFormat(documentType)

                    viewModel.updateProfile(
                        context = context,
                        firstName = firstName,
                        lastName = lastName,
                        phone = phone,
                        address = address,
                        documentType = backendDocumentType,
                        documentNumber = documentNumber,
                        birthDate = birthDate,
                        postalCode = postalCode,
                        country = country
                    )
                }
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileForm(
    firstName: String,
    lastName: String,
    documentType: String,
    documentNumber: String,
    documentHint: String,
    birthDate: String,
    phone: String,
    postalCode: String,
    country: String,
    address: String,
    validationErrors: Map<String, String>,
    onFirstNameChange: (String) -> Unit,
    onLastNameChange: (String) -> Unit,
    onDocumentTypeChange: (String) -> Unit,
    onDocumentNumberChange: (String) -> Unit,
    onBirthDateChange: (String) -> Unit,
    onPhoneChange: (String) -> Unit,
    onPostalCodeChange: (String) -> Unit,
    onCountryChange: (String) -> Unit,
    onAddressChange: (String) -> Unit,
    isLoading: Boolean,
    onSaveClick: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        // Sección de foto
        ProfilePhotoSection()

        Spacer(modifier = Modifier.height(24.dp))

        // Nombres y Apellidos
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedTextField(
                value = firstName,
                onValueChange = onFirstNameChange,
                label = { Text("Nombres *") },
                modifier = Modifier.weight(1f),
                enabled = !isLoading,
                isError = validationErrors.containsKey("firstName"),
                supportingText = {
                    validationErrors["firstName"]?.let { error ->
                        Text(text = error, color = MaterialTheme.colorScheme.error)
                    }
                }
            )
            OutlinedTextField(
                value = lastName,
                onValueChange = onLastNameChange,
                label = { Text("Apellidos *") },
                modifier = Modifier.weight(1f),
                enabled = !isLoading,
                isError = validationErrors.containsKey("lastName"),
                supportingText = {
                    validationErrors["lastName"]?.let { error ->
                        Text(text = error, color = MaterialTheme.colorScheme.error)
                    }
                }
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Tipo Documento y Número
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Dropdown para tipo de documento
            var expanded by remember { mutableStateOf(false) }
            val documentTypes = listOf("DNI", "Pasaporte", "Carnet de Extranjería")

            ExposedDropdownMenuBox(
                expanded = expanded,
                onExpandedChange = { expanded = !expanded },
                modifier = Modifier.weight(1f)
            ) {
                OutlinedTextField(
                    value = documentType,
                    onValueChange = {},
                    readOnly = true,
                    label = { Text("Tipo Documento *") },
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                    modifier = Modifier.menuAnchor(),
                    enabled = !isLoading,
                    isError = validationErrors.containsKey("documentType"),
                    supportingText = {
                        validationErrors["documentType"]?.let { error ->
                            Text(text = error, color = MaterialTheme.colorScheme.error)
                        }
                    },
                    placeholder = { Text("Seleccionar") }
                )
                ExposedDropdownMenu(
                    expanded = expanded,
                    onDismissRequest = { expanded = false }
                ) {
                    documentTypes.forEach { tipo ->
                        DropdownMenuItem(
                            text = { Text(tipo) },
                            onClick = {
                                onDocumentTypeChange(tipo)
                                expanded = false
                            }
                        )
                    }
                }
            }

            OutlinedTextField(
                value = documentNumber,
                onValueChange = onDocumentNumberChange,
                label = { Text("Número *") },
                modifier = Modifier.weight(1f),
                enabled = !isLoading && documentType.isNotEmpty(),
                isError = validationErrors.containsKey("documentNumber"),
                supportingText = {
                    if (validationErrors.containsKey("documentNumber")) {
                        Text(
                            text = validationErrors["documentNumber"] ?: "",
                            color = MaterialTheme.colorScheme.error
                        )
                    } else {
                        Text(text = documentHint, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                },
                placeholder = { Text(documentHint) }
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Fecha de Nacimiento
        OutlinedTextField(
            value = birthDate,
            onValueChange = onBirthDateChange,
            label = { Text("Fecha Nacimiento") },
            modifier = Modifier.fillMaxWidth(),
            enabled = !isLoading,
            isError = validationErrors.containsKey("birthDate"),
            supportingText = {
                validationErrors["birthDate"]?.let { error ->
                    Text(text = error, color = MaterialTheme.colorScheme.error)
                } ?: Text("Formato: dd/mm/yyyy", color = MaterialTheme.colorScheme.onSurfaceVariant)
            },
            placeholder = { Text("01/01/1990") }
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Teléfono
        OutlinedTextField(
            value = phone,
            onValueChange = onPhoneChange,
            label = { Text("Celular *") },
            modifier = Modifier.fillMaxWidth(),
            enabled = !isLoading,
            prefix = { Text("+51 ") },
            isError = validationErrors.containsKey("phone"),
            supportingText = {
                validationErrors["phone"]?.let { error ->
                    Text(text = error, color = MaterialTheme.colorScheme.error)
                } ?: Text("9 dígitos (Ej: 987654321)", color = MaterialTheme.colorScheme.onSurfaceVariant)
            },
            placeholder = { Text("987654321") }
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Código Postal y País
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedTextField(
                value = postalCode,
                onValueChange = onPostalCodeChange,
                label = { Text("Código Postal") },
                modifier = Modifier.weight(1f),
                enabled = !isLoading
            )
            OutlinedTextField(
                value = country,
                onValueChange = onCountryChange,
                label = { Text("País") },
                modifier = Modifier.weight(1f),
                enabled = !isLoading
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Dirección
        OutlinedTextField(
            value = address,
            onValueChange = onAddressChange,
            label = { Text("Dirección") },
            modifier = Modifier.fillMaxWidth(),
            enabled = !isLoading,
            minLines = 2
        )

        Spacer(modifier = Modifier.height(32.dp))

        // Botón Guardar
        Button(
            onClick = onSaveClick,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            enabled = !isLoading &&
                    firstName.isNotEmpty() &&
                    lastName.isNotEmpty() &&
                    phone.isNotEmpty() &&
                    documentType.isNotEmpty() &&
                    documentNumber.isNotEmpty()
        ) {
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    color = MaterialTheme.colorScheme.onPrimary
                )
            } else {
                Text("Guardar Cambios")
            }
        }
    }
}

// Helper: mapear etiqueta UI -> valor backend
private fun mapDocumentTypeToBackendFormat(documentTypeLabel: String): String? {
    return when (documentTypeLabel) {
        "DNI" -> "dni"
        "Pasaporte" -> "pasaporte"
        "Carnet de Extranjería" -> "carnet_extranjeria"
        else -> null
    }
}
