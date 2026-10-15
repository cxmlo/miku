package expo.modules.mikuintent

import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition

class MikuIntentModule : Module() {
  override fun definition() = ModuleDefinition {
    Name("MikuIntent")

    Function("getIntentAction") {
      val activity = appContext.currentActivity
      return@Function activity?.intent?.action
    }
  }
}
