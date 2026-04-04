```
lib/
│
├── core/                              # Global foundation (STRICTLY SHARED)
│
│   ├── config/                        # App-level configuration
│   │   ├── app_config.dart            # env, app constants
│   │   └── env.dart                   # dev/staging/prod switch
│   │
│   ├── network/                       # API layer (CENTRALIZED)
│   │   ├── api_client.dart            # Dio/HTTP client
│   │   ├── api_endpoints.dart         # ALL endpoints in one place
│   │   ├── api_config.dart            # base URL, headers
│   │   ├── interceptors.dart          # auth, logging
│   │   └── api_exception.dart         # error handling
│   │
│   ├── theme/                         # FULL THEME CONTROL
│   │   ├── app_theme.dart             # wraps MaterialTheme
│   │   ├── color_schemes.dart         # extracted from your theme.dart
│   │   ├── text_theme.dart            # from util.dart
│   │   └── theme_provider.dart        # Riverpod theme controller
│   │
│   ├── router/                        # Navigation (CENTRALIZED)
│   │   ├── app_router.dart
│   │   └── route_names.dart
│   │
│   ├── providers/                     # GLOBAL RIVERPOD UTILITIES
│   │   ├── app_provider.dart          # global app state
│   │   ├── auth_provider.dart         # JWT + session
│   │   └── network_provider.dart      # api client provider
│   │
│   ├── constants/                     # Static values
│   │   └── app_constants.dart
│   │
│   └── utils/                         # Pure helper functions
│       └── helpers.dart
│
├── features/                          # FEATURE-FIRST ARCHITECTURE
│
│   ├── auth/
│   │   ├── data/
│   │   │   └── auth_api.dart          # uses centralized endpoints
│   │   │
│   │   ├── provider/
│   │   │   └── auth_feature_provider.dart
│   │   │
│   │   └── presentation/
│   │       ├── login_screen.dart
│   │       ├── register_screen.dart
│   │       └── otp_screen.dart
│
│   ├── dashboard/
│   │   ├── provider/
│   │   │   └── dashboard_provider.dart
│   │   │
│   │   └── presentation/
│   │       └── dashboard_screen.dart
│
│   ├── policy/
│   │   ├── data/
│   │   │   └── policy_api.dart
│   │   │
│   │   ├── provider/
│   │   │   └── policy_provider.dart
│   │   │
│   │   └── presentation/
│   │       └── policy_screen.dart
│
│   ├── claims/
│   │   ├── data/
│   │   │   └── claims_api.dart
│   │   │
│   │   ├── provider/
│   │   │   └── claims_provider.dart
│   │   │
│   │   └── presentation/
│   │       └── claims_screen.dart
│
│   ├── payout/
│   │   ├── data/
│   │   │   └── payout_api.dart
│   │   │
│   │   ├── provider/
│   │   │   └── payout_provider.dart
│   │   │
│   │   └── presentation/
│   │       └── payout_screen.dart
│
│   ├── profile/
│   │   ├── data/
│   │   │   └── profile_api.dart
│   │   │
│   │   ├── provider/
│   │   │   └── profile_provider.dart
│   │   │
│   │   └── presentation/
│   │       └── profile_screen.dart
│
├── shared/                            # PURE REUSABLE UI ONLY
│   ├── widgets/
│   │   ├── app_button.dart
│   │   ├── app_loader.dart
│   │   ├── app_card.dart
│   │   └── app_textfield.dart
│   │
│   └── models/
│       └── common_models.dart
│
├── main.dart
```