package com.susmitawedsashish.formfiller

import android.app.assist.AssistStructure.ViewNode
import android.text.InputType
import android.view.View

/** Works out which [Field] (if any) a view in another app's form represents. */
object FieldMatcher {

    // Hints apps can declare explicitly via android:autofillHints.
    private val hintMap = mapOf(
        View.AUTOFILL_HINT_NAME to Field.NAME,
        "personName" to Field.NAME,
        View.AUTOFILL_HINT_EMAIL_ADDRESS to Field.EMAIL,
        View.AUTOFILL_HINT_PHONE to Field.PHONE,
        "phoneNumber" to Field.PHONE,
        View.AUTOFILL_HINT_POSTAL_ADDRESS to Field.ADDRESS,
        "streetAddress" to Field.ADDRESS,
        "addressLocality" to Field.CITY,
        View.AUTOFILL_HINT_POSTAL_CODE to Field.POSTAL_CODE,
    )

    // Fallback keywords searched for in the view's id, hint and label text.
    // Order matters: the first matching entry wins.
    private val keywordMap = listOf(
        Field.EMAIL to listOf("email", "e-mail"),
        Field.PHONE to listOf("phone", "mobile", "tel", "contact number"),
        Field.POSTAL_CODE to listOf("zip", "postal", "postcode", "pincode", "pin code"),
        Field.CITY to listOf("city", "town"),
        Field.ADDRESS to listOf("address", "street"),
        Field.NAME to listOf("name"),
    )

    // Never fill these, even if they mention "name" (e.g. "username").
    private val excluded = listOf("user", "login", "password", "company", "nick")

    fun match(node: ViewNode): Field? {
        if (node.autofillId == null || node.autofillType != View.AUTOFILL_TYPE_TEXT) return null
        if (isPassword(node.inputType)) return null

        node.autofillHints?.firstNotNullOfOrNull { hintMap[it] }?.let { return it }

        val text = listOfNotNull(node.idEntry, node.hint, node.text?.toString(), node.contentDescription?.toString())
            .joinToString(" ")
            .lowercase()
        if (excluded.none { it in text }) {
            keywordMap.firstOrNull { (_, words) -> words.any { it in text } }?.let { return it.first }
        }

        return fromInputType(node.inputType)
    }

    private fun fromInputType(inputType: Int): Field? {
        if (inputType and InputType.TYPE_MASK_CLASS == InputType.TYPE_CLASS_PHONE) return Field.PHONE
        if (inputType and InputType.TYPE_MASK_CLASS != InputType.TYPE_CLASS_TEXT) return null
        return when (inputType and InputType.TYPE_MASK_VARIATION) {
            InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS,
            InputType.TYPE_TEXT_VARIATION_WEB_EMAIL_ADDRESS -> Field.EMAIL
            InputType.TYPE_TEXT_VARIATION_PERSON_NAME -> Field.NAME
            InputType.TYPE_TEXT_VARIATION_POSTAL_ADDRESS -> Field.ADDRESS
            else -> null
        }
    }

    private fun isPassword(inputType: Int): Boolean {
        val variation = inputType and InputType.TYPE_MASK_VARIATION
        return when (inputType and InputType.TYPE_MASK_CLASS) {
            InputType.TYPE_CLASS_TEXT -> variation == InputType.TYPE_TEXT_VARIATION_PASSWORD ||
                variation == InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD ||
                variation == InputType.TYPE_TEXT_VARIATION_WEB_PASSWORD
            InputType.TYPE_CLASS_NUMBER -> variation == InputType.TYPE_NUMBER_VARIATION_PASSWORD
            else -> false
        }
    }
}
