package com.susmitawedsashish.formfiller

import android.content.Context

/** The kinds of form fields Form Filler knows how to fill. */
enum class Field(val prefKey: String) {
    NAME("name"),
    EMAIL("email"),
    PHONE("phone"),
    ADDRESS("address"),
    CITY("city"),
    POSTAL_CODE("postal_code"),
}

/** The user's saved details, persisted in SharedPreferences. */
class Profile(context: Context) {
    private val prefs = context.getSharedPreferences("profile", Context.MODE_PRIVATE)

    operator fun get(field: Field): String = prefs.getString(field.prefKey, "").orEmpty()

    fun save(values: Map<Field, String>) {
        prefs.edit().apply {
            values.forEach { (field, value) -> putString(field.prefKey, value.trim()) }
        }.apply()
    }

    fun isEmpty(): Boolean = Field.entries.all { get(it).isBlank() }
}
