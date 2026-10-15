const { withAndroidManifest, withMainActivity, withAndroidStyles } = require('@expo/config-plugins');

function withAssistantManifest(config) {
  return withAndroidManifest(config, (config) => {
    const manifest = config.modResults;
    const mainActivity = manifest.manifest.application[0].activity.find(
      (a) => a.$['android:name'] === '.MainActivity'
    );

    if (mainActivity) {
      // Set Theme to Transparent
      mainActivity.$['android:theme'] = '@style/Theme.App.Transparent';
      mainActivity.$['android:launchMode'] = 'singleTask';

      // Add Intent Filter for ASSIST
      if (!mainActivity['intent-filter']) {
        mainActivity['intent-filter'] = [];
      }
      
      const hasAssist = mainActivity['intent-filter'].some((f) => 
        f.action && f.action.some((a) => a.$['android:name'] === 'android.intent.action.ASSIST')
      );

      if (!hasAssist) {
        mainActivity['intent-filter'].push({
          action: [
            { $: { 'android:name': 'android.intent.action.ASSIST' } },
            { $: { 'android:name': 'android.intent.action.VOICE_COMMAND' } }
          ],
          category: [
            { $: { 'android:name': 'android.intent.category.DEFAULT' } }
          ]
        });
      }
    }
    return config;
  });
}

function withAssistantStyles(config) {
  return withAndroidStyles(config, (config) => {
    const styles = config.modResults;
    
    const hasTransparentTheme = styles.resources.style.some(s => s.$.name === 'Theme.App.Transparent');
    
    if (!hasTransparentTheme) {
      styles.resources.style.push({
        $: { name: 'Theme.App.Transparent', parent: 'Theme.AppCompat.Light.NoActionBar' },
        item: [
          { $: { name: 'android:windowIsTranslucent' }, _: 'true' },
          { $: { name: 'android:windowBackground' }, _: '@android:color/transparent' },
          { $: { name: 'android:windowContentOverlay' }, _: '@null' },
          { $: { name: 'android:windowNoTitle' }, _: 'true' },
          { $: { name: 'android:windowIsFloating' }, _: 'false' },
          { $: { name: 'android:backgroundDimEnabled' }, _: 'false' }
        ]
      });
    }
    return config;
  });
}

function withAssistantMainActivity(config) {
  return withMainActivity(config, (config) => {
    let contents = config.modResults.contents;
    
    if (!contents.includes('import android.os.Bundle')) {
      contents = contents.replace('import android.os.Build', 'import android.os.Build\nimport android.os.Bundle');
    }

    if (contents.includes('override fun createReactActivityDelegate(): ReactActivityDelegate {') && !contents.includes('options.putString("intentAction", intent.action)')) {
      const target = 'override fun createReactActivityDelegate(): ReactActivityDelegate {';
      const replacement = `
  override fun createReactActivityDelegate(): ReactActivityDelegate {
    return object : DefaultReactActivityDelegate(this, mainComponentName, fabricEnabled) {
      override fun getLaunchOptions(): Bundle? {
        val options = super.getLaunchOptions() ?: Bundle()
        options.putString("intentAction", intent.action)
        return options
      }
    }
  }

  // Original overridden function follows as comment:
  // `;
      contents = contents.replace(target, replacement);
    }
    config.modResults.contents = contents;
    return config;
  });
}

module.exports = function withAssistant(config) {
  config = withAssistantManifest(config);
  config = withAssistantStyles(config);
  // We no longer modify MainActivity.kt here. We use the custom miku-intent native module instead.
  return config;
};
