const posts = [
  {
    id: "reel",
    image: "assets/posts/post-01-reel-cover.jpg",
    video: "assets/video/intro.mp4",
    badge: "▶",
    likes: 428,
    caption:
      "A complete HCP strategy used to take weeks. Evidence scattered. Insights untested. Messaging guessed. STRATA is the AI Strategy Director for HCP campaigns — it writes the working file before anyone sees a slide. Every claim traces to named evidence. Nothing is invented. Try it free.",
  },
  {
    id: "problem",
    image: "assets/posts/post-02-problem.jpg",
    likes: 216,
    caption:
      "The existing problem is not a shortage of slides. Decks get built before the thinking is done. Papers sit in folders. Advisory-board notes contradict the field. Messaging is guessed to a deadline. STRATA exists to end that sequence.",
  },
  {
    id: "what",
    image: "assets/posts/post-03-what.jpg",
    likes: 301,
    caption:
      "What the app is: an AI Strategy Director for healthcare-professional campaigns. Upload any brief. It extracts the working file, picks a doctrine from the tension in the brief, and only then makes the deck and the measurement room.",
  },
  {
    id: "doctrine",
    image: "assets/posts/post-04-doctrine.jpg",
    likes: 274,
    caption:
      "Generic tools write a funnel. STRATA picks a doctrine. For the CardioShield example that doctrine is First-Touch: the enemy is the stabilise-first ritual, not the comparator molecule. That is why it is one of a kind.",
  },
  {
    id: "evidence",
    image: "assets/posts/post-05-evidence.jpg",
    likes: 198,
    caption:
      "Evidence first. Brand-generated, independent, evolving, guideline, and health-economic streams stay separated and graded. If a claim has no named source it is logged as a gap — never invented.",
  },
  {
    id: "working",
    image: "assets/posts/post-06-working-file.jpg",
    likes: 187,
    caption:
      "The working file is written before anyone sees a slide. Doctrine, bet, evidence, discordance, behavioural drivers, then messaging. The deck is a consequence of the thinking, not a substitute for it.",
  },
  {
    id: "deck",
    image: "assets/posts/post-07-deck.jpg",
    likes: 233,
    caption:
      "A client-ready strat deck: forest plots, impact matrices, message house, engagement journey. Download PPTX. Print to PDF. Still flagged for MLR before it meets a doctor.",
  },
  {
    id: "papers",
    image: "assets/posts/post-08-papers.jpg",
    likes: 164,
    caption:
      "Papers, not slogans. The campaign lead is the highest-leverage published source — DOI or PMID — not the line that sounds best in a war room.",
  },
  {
    id: "measure",
    image: "assets/posts/post-09-measurement.jpg",
    likes: 141,
    caption:
      "Measurement from engagement activity down to quarterly revenue. KPI tree, kill-criteria, governance. Planning numbers stay labelled illustrative until you replace them with audit baselines.",
  },
  {
    id: "mlr",
    image: "assets/posts/post-10-mlr.jpg",
    likes: 156,
    caption:
      "MLR-aware by design. Compatible with pharmaceutical promotion codes. No inducements. No off-label. Everything that needs review is flagged before it leaves the working file.",
  },
  {
    id: "unique",
    image: "assets/posts/post-11-unique.jpg",
    likes: 312,
    caption:
      "One of a kind: doctrine not a funnel. Working file before slides. Named evidence only. One continuous 11-phase reasoning thread, so messaging can cite the exact evidence row that earned it.",
  },
  {
    id: "cta",
    image: "assets/posts/post-12-cta.jpg",
    likes: 509,
    caption:
      "Try STRATA free. Start your first strategy this afternoon. Link in bio — or tap Try for free.",
  },
];

const highlights = {
  brief: [
    {
      image: "assets/posts/post-03-what.jpg",
      text: "STRATA is the AI Strategy Director for HCP campaigns.",
    },
    {
      image: "assets/posts/post-02-problem.jpg",
      text: "It exists because decks still get built before the thinking is done.",
    },
  ],
  doctrine: [
    {
      image: "assets/posts/post-04-doctrine.jpg",
      text: "Not a funnel. A doctrine picked from the tension in your brief.",
    },
    {
      image: "assets/posts/post-06-working-file.jpg",
      text: "The working file is written before anyone sees a slide.",
    },
  ],
  evidence: [
    {
      image: "assets/posts/post-05-evidence.jpg",
      text: "Every claim traces to named evidence. Gaps stay gaps.",
    },
    {
      image: "assets/posts/post-08-papers.jpg",
      text: "The campaign lead is a paper — DOI or PMID — not a slogan.",
    },
  ],
  deck: [
    {
      image: "assets/posts/post-07-deck.jpg",
      text: "Then, and only then, the client-ready strat deck.",
    },
    {
      image: "assets/posts/post-09-measurement.jpg",
      text: "Measurement from engagement to quarterly revenue.",
    },
  ],
  try: [
    {
      image: "assets/posts/post-12-cta.jpg",
      text: "Try STRATA free. Start your first strategy.",
    },
    {
      image: "assets/posts/post-11-unique.jpg",
      text: "Doctrine. Evidence. One continuous thread. Nothing else does this.",
    },
  ],
};

const video = document.getElementById("intro-video");
const bar = document.getElementById("progress-bar");
const soundBtn = document.getElementById("toggle-sound");
const skipBtn = document.getElementById("skip-intro");
const replayBtn = document.getElementById("replay-intro");
const grid = document.getElementById("posts-grid");
const reelsPanel = document.getElementById("reels-panel");
const overlay = document.getElementById("post-overlay");
const storyOverlay = document.getElementById("story-overlay");

let storyKey = "brief";
let storyIndex = 0;

function showProfile() {
  document.body.classList.remove("view-intro");
  document.body.classList.add("view-profile");
  video.pause();
  window.scrollTo(0, 0);
}

function showIntro() {
  document.body.classList.add("view-intro");
  document.body.classList.remove("view-profile");
  video.currentTime = 0;
  video.play().catch(() => {});
}

function setMuted(muted) {
  video.muted = muted;
  soundBtn.querySelector("span").textContent = muted ? "Sound" : "Mute";
}

async function startFilm() {
  video.muted = true;
  try {
    await video.play();
  } catch {
    /* autoplay can be blocked; poster + skip still work */
  }
}

document.querySelector(".intro-stage").addEventListener("click", async () => {
  setMuted(false);
  try {
    await video.play();
  } catch {
    /* ignore */
  }
});

video.addEventListener("timeupdate", () => {
  if (!video.duration) return;
  bar.style.width = `${(video.currentTime / video.duration) * 100}%`;
});

video.addEventListener("ended", showProfile);
skipBtn.addEventListener("click", showProfile);
replayBtn.addEventListener("click", showIntro);
soundBtn.addEventListener("click", () => setMuted(!video.muted));

document.getElementById("follow-btn").addEventListener("click", (event) => {
  event.currentTarget.classList.toggle("is-on");
  event.currentTarget.textContent = event.currentTarget.classList.contains("is-on")
    ? "Following"
    : "Follow";
});

document.getElementById("share-profile").addEventListener("click", async () => {
  const url = window.location.href;
  try {
    await navigator.clipboard.writeText(url);
    document.getElementById("share-profile").textContent = "✓";
  } catch {
    window.prompt("Copy this page link", url);
  }
});

function renderGrid() {
  grid.innerHTML = posts
    .map(
      (post) => `
      <button type="button" data-post="${post.id}">
        <img src="${post.image}" alt="">
        ${post.badge ? `<span class="badge">${post.badge}</span>` : ""}
        <span class="hover">♥ ${post.likes}</span>
      </button>`,
    )
    .join("");

  reelsPanel.innerHTML = `
    <button type="button" data-post="reel">
      <img src="assets/video/poster.jpg" alt="">
      <span>Intro · 0:31</span>
    </button>`;
}

function openPost(id) {
  const post = posts.find((item) => item.id === id);
  if (!post) return;
  const image = document.getElementById("post-image");
  const media = document.getElementById("post-video");
  document.getElementById("post-caption").textContent = post.caption;
  if (post.video) {
    image.hidden = true;
    media.hidden = false;
    media.src = post.video;
    media.play().catch(() => {});
  } else {
    media.pause();
    media.hidden = true;
    image.hidden = false;
    image.src = post.image;
  }
  overlay.hidden = false;
}

function closeOverlays() {
  overlay.hidden = true;
  storyOverlay.hidden = true;
  const media = document.getElementById("post-video");
  media.pause();
}

function renderStory() {
  const slides = highlights[storyKey];
  const slide = slides[storyIndex];
  document.getElementById("story-title").textContent = `STRATA · ${storyKey}`;
  document.getElementById("story-image").src = slide.image;
  document.getElementById("story-text").textContent = slide.text;
  document.getElementById("story-bars").innerHTML = slides
    .map((_, index) => `<i class="${index <= storyIndex ? "on" : ""}"></i>`)
    .join("");
}

function openHighlight(key) {
  storyKey = key;
  storyIndex = 0;
  renderStory();
  storyOverlay.hidden = false;
}

grid.addEventListener("click", (event) => {
  const button = event.target.closest("[data-post]");
  if (button) openPost(button.dataset.post);
});

reelsPanel.addEventListener("click", (event) => {
  const button = event.target.closest("[data-post]");
  if (button) openPost(button.dataset.post);
});

document.querySelector(".highlights").addEventListener("click", (event) => {
  const button = event.target.closest("[data-highlight]");
  if (button) openHighlight(button.dataset.highlight);
});

document.querySelectorAll("[data-close]").forEach((button) => {
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    closeOverlays();
  });
});

document.getElementById("story-next").addEventListener("click", () => {
  const slides = highlights[storyKey];
  if (storyIndex < slides.length - 1) {
    storyIndex += 1;
    renderStory();
  } else {
    closeOverlays();
  }
});

document.getElementById("story-prev").addEventListener("click", () => {
  if (storyIndex > 0) {
    storyIndex -= 1;
    renderStory();
  } else {
    closeOverlays();
  }
});

document.querySelector(".tabs").addEventListener("click", (event) => {
  const button = event.target.closest("[data-tab]");
  if (!button) return;
  document.querySelectorAll(".tabs button").forEach((tab) => {
    tab.classList.toggle("active", tab === button);
    tab.setAttribute("aria-selected", tab === button ? "true" : "false");
  });
  document.querySelectorAll("[data-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.panel !== button.dataset.tab;
  });
});

overlay.addEventListener("click", (event) => {
  if (event.target === overlay) closeOverlays();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeOverlays();
});

renderGrid();
startFilm();
