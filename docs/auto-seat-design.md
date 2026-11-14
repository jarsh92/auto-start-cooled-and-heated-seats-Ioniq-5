# Auto Seat UI redesign

Status: approved visual direction; app implementation and in-car validation pending. This proposal does not change the installed app or declare a stable release.

## Approved appearance

- Graphite + Ford Blue (palette 1).
- Dark background with an opaque graphite panel, warm white text, and deep blue active controls.
- Compact rounded picture-frame panel centered horizontally on the head unit display.
- Target apparent panel width: approximately 5.5–6 inches on the actual head unit. Confirm the physical size in the car rather than assuming browser pixels correspond to inches.
- Buttons contained within the panel, with comfortable touch targets and no full-screen stretching.
- A simple white seat outline in the header.
- Matching launcher icon: white seat outline, graphite background, restrained Ford Blue accent.

## Interactive prototype

Download `auto-seat-ui-preview.html` from this directory and open it in a browser. It uses Lucide 0.468.0 from a CDN for a provisional chair glyph; the controls work without that resource, but the glyph needs internet access. This is not the final seat artwork.

The prototype demonstrates the appearance, seat selection, automatic-mode switches, and settings navigation. These controls are illustrative, run only in the browser, and do not communicate with a vehicle. Match the final screens to the real app's settings and behavior during implementation.

## Release preparation

1. Recover and verify the current app source and build inputs; do not rebuild from the repository's older 1.6.0 package by assumption.
2. Integrate the approved panel, palette, seat artwork, and launcher icon into the actual app.
3. Audit the Auto Seat display name, filenames, directories, startup references, and migration behavior; retain existing settings.
4. Verify the build and installation package, then validate layout, startup, saved settings, and existing seat/steering-wheel functions in the car.
5. Publish the verified source, build instructions, compatibility details, and an accurately labeled prerelease. Mark stable only after validation.

## Attribution and licensing

The existing README states that this project derives from another user's package. Preserve upstream credit and identify the original source and license before adding a project-wide license or redistributing additional upstream materials. Public repository visibility alone does not grant an open-source license.
