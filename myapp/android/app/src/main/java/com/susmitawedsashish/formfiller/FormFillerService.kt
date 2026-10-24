package com.susmitawedsashish.formfiller

import android.app.assist.AssistStructure
import android.os.CancellationSignal
import android.service.autofill.AutofillService
import android.service.autofill.Dataset
import android.service.autofill.FillCallback
import android.service.autofill.FillRequest
import android.service.autofill.FillResponse
import android.service.autofill.SaveCallback
import android.service.autofill.SaveRequest
import android.view.autofill.AutofillId
import android.view.autofill.AutofillValue
import android.widget.RemoteViews

/**
 * Autofill service that offers the saved [Profile] whenever another app shows a
 * form with recognisable fields (name, email, phone, address, ...).
 */
class FormFillerService : AutofillService() {

    override fun onFillRequest(
        request: FillRequest,
        cancellationSignal: CancellationSignal,
        callback: FillCallback,
    ) {
        val structure = request.fillContexts.last().structure
        // Don't offer to fill our own profile editor.
        if (structure.activityComponent.packageName == packageName) {
            callback.onSuccess(null)
            return
        }

        val profile = Profile(this)
        val fields = findFields(structure).filterValues { profile[it].isNotBlank() }
        if (fields.isEmpty()) {
            callback.onSuccess(null)
            return
        }

        val presentation = RemoteViews(packageName, android.R.layout.simple_list_item_1).apply {
            setTextViewText(android.R.id.text1, getString(R.string.fill_with_profile))
        }
        val dataset = Dataset.Builder(presentation).apply {
            fields.forEach { (id, field) -> setValue(id, AutofillValue.forText(profile[field])) }
        }.build()

        callback.onSuccess(FillResponse.Builder().addDataset(dataset).build())
    }

    // We never declare SaveInfo, so this is not expected to be called.
    override fun onSaveRequest(request: SaveRequest, callback: SaveCallback) {
        callback.onSuccess()
    }

    private fun findFields(structure: AssistStructure): Map<AutofillId, Field> {
        val found = linkedMapOf<AutofillId, Field>()
        fun visit(node: AssistStructure.ViewNode) {
            FieldMatcher.match(node)?.let { found[node.autofillId!!] = it }
            for (i in 0 until node.childCount) visit(node.getChildAt(i))
        }
        for (i in 0 until structure.windowNodeCount) visit(structure.getWindowNodeAt(i).rootViewNode)
        return found
    }
}
