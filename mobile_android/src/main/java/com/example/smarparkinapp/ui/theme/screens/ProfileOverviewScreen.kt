package com.example.smarparkinapp.ui.theme.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CreditCard
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Card
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.Button
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.smarparkinapp.R
import com.example.smarparkinapp.ui.theme.viewmodel.ProfileViewModel
import androidx.compose.foundation.shape.RoundedCornerShape

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileOverviewScreen(
    onBack: () -> Unit,
    onEditProfile: () -> Unit,
    onPaymentMethods: () -> Unit,
    onMyVehicles: () -> Unit,
    onMiPerfilTab: () -> Unit = {},
    viewModel: ProfileViewModel = viewModel()
) {
    val context = LocalContext.current
    val userProfile by viewModel.userProfile.collectAsState(initial = null)
    val isLoading by viewModel.isLoading.collectAsState()
    val errorMessage by viewModel.errorMessage.collectAsState()

    // Cargar el perfil al entrar
    LaunchedEffect(Unit) {
        viewModel.loadUserProfile(context)
    }

    Scaffold(
        topBar = {
            CenterAlignedTopAppBar(
                title = { Text("Información de Perfil") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.Person, contentDescription = "Volver")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(padding)
        ) {
            // Header azul con avatar y nombre
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(180.dp)
                    .background(MaterialTheme.colorScheme.primaryContainer),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    val avatarModifier = Modifier
                        .size(88.dp)
                        .clip(CircleShape)
                        .background(MaterialTheme.colorScheme.surface)

                    // Usamos placeholder (drawable) para evitar errores si no existe campo avatarUrl
                    Image(
                        painter = painterResource(R.drawable.ic_avatar_placeholder),
                        contentDescription = "Avatar",
                        modifier = avatarModifier,
                        contentScale = ContentScale.Crop
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    Text(
                        text = userProfile?.firstName?.let { fn ->
                            "${fn} ${userProfile?.lastName ?: ""}".trim()
                        } ?: (userProfile?.username ?: "Usuario"),
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Medium),
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Email y acciones
            Column(modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp)
            ) {
                // Email
                userProfile?.email?.let { email ->
                    Text(text = "Correo electrónico", color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(text = email, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurface)
                    Spacer(modifier = Modifier.height(12.dp))
                }

                // Opciones: Actualizar mis datos / Métodos de Pago
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onEditProfile() },
                    shape = RoundedCornerShape(8.dp),
                    colors = CardDefaults.cardColors()
                ) {
                    Row(modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Default.Edit, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                        Spacer(modifier = Modifier.width(12.dp))
                        Text(text = "Actualizar mis datos", modifier = Modifier.weight(1f))
                        Icon(Icons.Default.Person, contentDescription = null)
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onPaymentMethods() },
                    shape = RoundedCornerShape(8.dp),
                    colors = CardDefaults.cardColors()
                ) {
                    Row(modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Default.CreditCard, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                        Spacer(modifier = Modifier.width(12.dp))
                        Text(text = "Métodos de Pago", modifier = Modifier.weight(1f))
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Tabs sencillas: Mi perfil | Mis vehículos
                var selectedTabIndex by remember { mutableStateOf(0) }
                val tabs = listOf("Mi perfil", "Mis vehículos")
                TabRow(selectedTabIndex = selectedTabIndex) {
                    tabs.forEachIndexed { index, title ->
                        Tab(selected = selectedTabIndex == index, onClick = {
                            selectedTabIndex = index
                            if (index == 0) onMiPerfilTab()
                            else onMyVehicles()
                        }) {
                            Text(text = title, modifier = Modifier.padding(12.dp))
                        }
                    }
                }

                Spacer(modifier = Modifier.height(12.dp))

                // Contenido del tab "Mi perfil" (datos básicos)
                if (selectedTabIndex == 0) {
                    Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(8.dp), colors = CardDefaults.cardColors()) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(text = "Teléfono", color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(text = userProfile?.phone ?: "-", style = MaterialTheme.typography.bodyMedium)
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(text = "Dirección", color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(text = userProfile?.address ?: "-", style = MaterialTheme.typography.bodyMedium)
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(text = "Tipo documento", color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(text = userProfile?.tipoDocumento ?: "-", style = MaterialTheme.typography.bodyMedium)
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(text = "Número documento", color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(text = userProfile?.numeroDocumento ?: "-", style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                } else {
                    // Contenido para "Mis vehículos" (puedes navegar a otra pantalla)
                    Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(8.dp), colors = CardDefaults.cardColors()) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(text = "Vehículos", style = MaterialTheme.typography.titleSmall)
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(text = "Ir a 'Mis vehículos' para ver y gestionar tus autos.")
                            Spacer(modifier = Modifier.height(8.dp))
                            Button(onClick = onMyVehicles) {
                                Text("Ver mis vehículos")
                            }
                        }
                    }
                }
            }
        }
    }
}
