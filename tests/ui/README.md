# Android 4.4 layout regression

Run `mvn test` in this directory with JDK 21 and Maven 3.9.9 (or compatible versions). Dependencies are public Maven Central/Google Android artifacts; internet access is required on first run. Configure Maven and Java networking for your environment when needed. Robolectric downloads its SDK runtime separately; an offline environment must prepopulate runtime dependencies.

The test measures the real MainActivity layout on SDK 19 at three viewport sizes, checks visible navigation and All off bounds, confirms nonzero body space, and exercises Settings/Ventilation tab visibility. It does not run vehicle commands. The previous spacer implementation fails the tab-bound assertion; fixed-height spacers pass.

This layout regression is not a substitute for testing the Hyundai head unit or physical controls.
