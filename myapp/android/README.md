# Form Filler (Android)

A minimal Android [Autofill service](https://developer.android.com/guide/topics/text/autofill-services)
that fills forms in other apps with details you save once.

## How it works

1. Open **Form Filler**, enter your name, email, phone, address, city and postal/PIN code, and tap **Save profile**.
2. Tap **Set as autofill service** and pick *Form Filler* in system settings.
3. In any app, focus a form field — a *Fill with saved profile* suggestion appears; tap it to fill every recognised field at once.

Fields are recognised (in this order) by:

- the `android:autofillHints` the app declares,
- keywords in the field's resource id, hint or label (`email`, `phone`, `zip`, `pincode`, `city`, `address`, `name`, ...),
- the field's `inputType` (email, phone, person name, postal address).

Password fields and things like `username` / `company name` are never filled.
The profile is stored locally in SharedPreferences and never leaves the device.

## Code

| File | Purpose |
| --- | --- |
| `MainActivity.kt` | Profile editor + shortcut to enable the service |
| `FormFillerService.kt` | `AutofillService` that walks the form and returns a dataset |
| `FieldMatcher.kt` | Heuristics mapping a view to a profile field |
| `Profile.kt` | The saved fields and their storage |

## Build

Requires the Android SDK (API 35) and JDK 17. Open this folder in Android Studio, or:

```sh
./gradlew installDebug
```

Minimum Android version is 8.0 (API 26), where the Autofill framework was introduced.
