const { withAndroidManifest } = require('@expo/config-plugins');

function withCleartextTraffic(config) {
  return withAndroidManifest(config, (config) => {
    const manifest = config.modResults;
    const application = manifest.manifest.application[0];
    
    // Force usesCleartextTraffic to true in the application tag
    application.$['android:usesCleartextTraffic'] = 'true';
    
    // Also add a network security config that allows all cleartext
    // This is the nuclear option for local network debugging
    application.$['android:networkSecurityConfig'] = '@xml/network_security_config';
    
    return config;
  });
}

module.exports = withCleartextTraffic;
