# Adapting Auto Seat — AI tools and contributors welcome

**Auto Seat additions were written by ChatGPT/Codex under Josh Waldmire's direction. No independent human code review has been completed.** Original upstream code/credit is Gregory Taylor's. Preserve LICENSE/CREDITS when reusing the MIT-licensed project.

You may use AI to inspect, explain, criticize, audit and fork the code, including investigating another vehicle. We welcome issues and contributions, including IONIQ 6 interest. Assistance offered by this project is AI-generated with ChatGPT/Codex; Josh supplies direction/testing, not independent engineering review. There is no promise of a port or compatibility. Human review is welcome and should be identified accurately if it occurs.

Start from the actual vehicle's region, model/year/trim, head-unit platform, firmware and equipment. Confirm framework/service contracts and value mappings from read-only evidence before proposing control changes. Do not bypass the build guard or test-actuate controls to detect equipment. A package that runs on one IONIQ 5 does not establish IONIQ 6 or another trim's compatibility. Keep private vehicle data and signing keys out of issues.

The current packager reuses the original signed APK; Android ID/helper paths are intentionally preserved. Changing Java source does not change the distributed APK. A modified app needs an explicit compatible signing/update plan; do not silently generate a replacement key or claim original-app update compatibility.

Planned equipment detection/trim overrides must distinguish unknown, absent and equipped states without actuation and must govern both UI and startup commands. A manual remembered configuration is a possible fallback. These features are not implemented in the current release. UI refinements and other vehicle adaptations have no committed schedule.

This post was prepared and posted with ChatGPT.
