/*
 * ─────────────────────────────────────────────────────────────
 *  JOE — SITE CONTENT
 *  This is the only file you need to edit to update the page.
 * ─────────────────────────────────────────────────────────────
 *
 *  How it works
 *  1. Replace a [PLACEHOLDER] with the real value, keeping the quotes.
 *  2. Anything still showing a [PLACEHOLDER] (or left empty "")
 *     is hidden from the public page automatically.
 *  3. To see what is still missing, open the page with ?edit
 *     on the end of the address, e.g.  index.html?edit
 *
 *  Never put private details here — everything in this file is public.
 */

window.SITE_CONTENT = {
  /* ── YouTube ─────────────────────────────────────────────── */

  // Your channel address, e.g. "https://www.youtube.com/@yourhandle"
  youtubeChannelUrl: "[YOUTUBE_CHANNEL_URL]",

  // Your introduction video, e.g. "https://www.youtube.com/watch?v=XXXXXXXXXXX"
  // (youtu.be/… and /shorts/… links work too)
  introVideoUrl: "[INTRO_VIDEO_URL]",

  // Optional: your own thumbnail image for the intro video.
  // Leave as "" to use the video's own YouTube thumbnail.
  introVideoThumbnail: "",

  // Short title read out by screen readers for the intro video.
  introVideoTitle: "Meet Joe — start here",

  /* ── Contact ─────────────────────────────────────────────── */

  // A public collaboration email (not your personal inbox).
  publicContactEmail: "[PUBLIC_CONTACT_EMAIL]",

  // Subject line pre-filled when someone taps the email button.
  emailSubject: "Collaboration idea",

  /* ── Optional social links ───────────────────────────────── */
  // Paste a full link to show it. Leave "" to hide it.
  socials: {
    instagram: "",
    tiktok: "",
    x: "",
    threads: "",
    linkedin: "",
    soundcloud: "",
    spotify: "",
    bandcamp: "",
  },

  /* ── Photographs ─────────────────────────────────────────── */
  // Put the files in  site/assets/photos/  then write the path here.
  // Leave "" to keep the typography-only design.
  // Best size: portrait 1200 × 1500 px JPG/WebP, under 250 KB.
  photos: {
    portrait: "",
    portraitAlt: "Joe in his studio",
    // Optional second photo for the About section, 1600 × 1000 px.
    studio: "",
    studioAlt: "Joe's studio in Worthing",
  },

  /* ── Current project ─────────────────────────────────────── */
  // Shown publicly only when BOTH title and description are filled in.
  currentProject: {
    title: "",
    status: "In progress", // e.g. "In progress", "Just started", "Finished"
    description: "",
    image: "", // e.g. "assets/photos/project.jpg" (1600 × 1000 px)
    imageAlt: "",
    videoUrl: "", // a YouTube link about this project
    videoLabel: "Watch the project video",
  },
};
