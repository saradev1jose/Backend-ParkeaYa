package com.example.smarparkinapp.ui.theme.screens

import androidx.compose.runtime.Composable
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.example.smarparkinapp.components.AddVehicleDialog
import com.example.smarparkinapp.screens.VehicleSelectionScreen
import com.example.smarparkinapp.ui.theme.viewmodel.ReservationViewModel
import com.example.smarparkinapp.ui.theme.data.model.ParkingLot
import com.example.smarparkinapp.ui.theme.screens.ReservationScreen
import com.example.smarparkinapp.ui.theme.screens.ProfileScreen
import com.example.smarparkinapp.ui.theme.screens.ProfileOverviewScreen
import com.example.smarparkinapp.ui.theme.viewmodel.ReservationViewModelFactory
import androidx.compose.ui.platform.LocalContext
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.ui.unit.dp
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.runtime.LaunchedEffect
import androidx.lifecycle.viewmodel.compose.viewModel as vm

@Composable
fun AppNavGraph(navController: NavHostController) {
    val context = LocalContext.current

    NavHost(
        navController = navController,
        startDestination = NavRoutes.Splash.route
    ) {
        // Splash
        composable(NavRoutes.Splash.route) {
            SplashScreen(
                onTimeout = { navController.navigate(NavRoutes.Login.route) }
            )
        }

        // Login
        composable(NavRoutes.Login.route) {
            LoginScreen(
                onLoginSuccess = { navController.navigate(NavRoutes.Home.route) },
                onRegisterClick = { navController.navigate(NavRoutes.Register.route) }
            )
        }

        // Register
        composable(NavRoutes.Register.route) {
            RegisterScreen(
                onRegisterSuccess = { userId ->
                    navController.navigate(NavRoutes.CompleteProfile.createRoute(userId)) {
                        popUpTo(NavRoutes.Register.route) { inclusive = true }
                    }
                },
                onLoginClick = { navController.navigate(NavRoutes.Login.route) }
            )
        }

        // Complete Profile
        composable(
            route = NavRoutes.CompleteProfile.route,
            arguments = listOf(navArgument("userId") { type = NavType.IntType })
        ) { backStackEntry ->
            val userId = backStackEntry.arguments?.getInt("userId") ?: 0
            CompleteProfileScreen(
                userId = userId,
                onProfileCompleted = {
                    navController.navigate(NavRoutes.Home.route) {
                        popUpTo(NavRoutes.Register.route) { inclusive = true }
                    }
                }
            )
        }

        // HOME
        composable(NavRoutes.Home.route) {
            HomeScreen(
                navController = navController,
                onParkingClick = { parkingId ->
                    navController.navigate(NavRoutes.ParkingDetail.createRoute(parkingId))
                },
                onReservationClick = { parkingId, vehicleId, startTime, endTime ->
                    navController.navigate(
                        NavRoutes.Reservation.createRoute(parkingId, vehicleId, startTime, endTime)
                    )
                }
            )
        }

        // Perfil - edit
        composable(NavRoutes.Perfil.route) {
            ProfileScreen(
                onBackClick = {
                    // Si quieres cerrar sesión o volver atrás
                    navController.navigate(NavRoutes.Login.route) {
                        popUpTo(NavRoutes.Home.route) { inclusive = true }
                    }
                }
            )
        }

        composable("profile_overview") {
            ProfileOverviewScreen(
                onBack = { navController.popBackStack() },
                onEditProfile = { navController.navigate("profile_edit") },
                onPaymentMethods = { navController.navigate("payment_methods") },
                onMyVehicles = { navController.navigate("my_vehicles") }
            )
        }

        // Destino explícito para la pantalla de edición de perfil
        composable("profile_edit") {
            ProfileScreen(
                onBackClick = { navController.popBackStack() }
            )
        }

        // Historial
        composable(NavRoutes.Historial.route) {
            HistoryScreen(navController = navController)
        }

        // Reservation
        composable(
            route = NavRoutes.Reservation.route,
            arguments = listOf(navArgument("parkingId") { type = NavType.IntType })
        ) { backStackEntry ->
            val parkingId = backStackEntry.arguments?.getInt("parkingId") ?: 0

            // TODO: Obtener el objeto ParkingLot completo desde tu API
            val parkingLot = ParkingLot(
                id = parkingId.toLong(),
                nombre = "Estacionamiento Temporal",
                direccion = "Dirección temporal",
                coordenadas = null,
                telefono = null,
                descripcion = null,
                horario_apertura = null,
                horario_cierre = null,
                nivel_seguridad = null,
                tarifa_hora = 5.0,
                total_plazas = 50,
                plazas_disponibles = 25,
                rating_promedio = null,
                total_resenas = null,
                aprobado = true,
                activo = true,
                dueno = null,
                esta_abierto = true,
                imagen_principal = null,
                dueno_nombre = null
            )

            val reservationViewModel: ReservationViewModel = viewModel(
                factory = ReservationViewModelFactory(context)
            )

            ReservationScreen(
                parking = parkingLot,
                onSuccessNavigate = {
                    navController.navigate(NavRoutes.Home.route) {
                        popUpTo(NavRoutes.Reservation.route) { inclusive = true }
                    }
                },
                onBack = { navController.popBackStack() }
            )
        }

        // Parking Detail
        composable(
            route = NavRoutes.ParkingDetail.route,
            arguments = listOf(navArgument("parkingId") { type = NavType.IntType })
        ) { backStackEntry ->
            val parkingId = backStackEntry.arguments?.getInt("parkingId") ?: 0

            ParkingDetailScreen(
                navController = navController,
                parkingId = parkingId
            )
        }

        // VEHICLE SELECTION - CORREGIDO
        composable(NavRoutes.VehicleSelection.route) {
            val viewModel: ReservationViewModel = viewModel(
                factory = ReservationViewModelFactory(context)
            )

            VehicleSelectionScreen(
                onBack = { navController.popBackStack() },
                onVehicleSelected = { car ->
                    // CORRECCIÓN: Especificar el tipo explícitamente
                    navController.previousBackStackEntry?.savedStateHandle?.set<Int>(
                        key = "selectedVehicleId",
                        car.id
                    )
                    navController.popBackStack()
                },
                onAddVehicle = {
                    viewModel.showAddVehicleForm()
                },
                viewModel = viewModel
            )

            if (viewModel.showAddVehicleDialog) {
                AddVehicleDialog(
                    viewModel = viewModel,
                    onDismiss = { viewModel.hideAddVehicleForm() },
                    onSave = { viewModel.saveNewVehicle() }
                )
            }
        }
    }
}
