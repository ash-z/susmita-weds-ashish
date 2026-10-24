package com.susmitawedsashish.formfiller

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.view.autofill.AutofillManager
import android.widget.Button
import android.widget.EditText
import android.widget.Toast

/** Lets the user edit their saved profile and enable the autofill service. */
class MainActivity : Activity() {

    private lateinit var profile: Profile
    private lateinit var inputs: Map<Field, EditText>
    private lateinit var enableButton: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        profile = Profile(this)

        inputs = mapOf(
            Field.NAME to findViewById(R.id.input_name),
            Field.EMAIL to findViewById(R.id.input_email),
            Field.PHONE to findViewById(R.id.input_phone),
            Field.ADDRESS to findViewById(R.id.input_address),
            Field.CITY to findViewById(R.id.input_city),
            Field.POSTAL_CODE to findViewById(R.id.input_postal_code),
        )
        if (savedInstanceState == null) {
            inputs.forEach { (field, input) -> input.setText(profile[field]) }
        }

        findViewById<Button>(R.id.button_save).setOnClickListener {
            profile.save(inputs.mapValues { (_, input) -> input.text.toString() })
            Toast.makeText(this, R.string.saved, Toast.LENGTH_SHORT).show()
        }

        enableButton = findViewById(R.id.button_enable)
        enableButton.setOnClickListener {
            val intent = Intent(Settings.ACTION_REQUEST_SET_AUTOFILL_SERVICE)
                .setData(Uri.parse("package:$packageName"))
            startActivity(intent)
        }
    }

    override fun onResume() {
        super.onResume()
        val enabled = getSystemService(AutofillManager::class.java)?.hasEnabledAutofillServices() == true
        enableButton.isEnabled = !enabled
        enableButton.setText(if (enabled) R.string.service_enabled else R.string.enable_service)
    }
}
