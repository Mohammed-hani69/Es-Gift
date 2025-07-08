const swiper = new Swiper(".swiper", {
  direction: "horizontal",
  spaceBetween: 20,
  loop: true,

  navigation: {
    nextEl: ".custom-next",
    prevEl: ".custom-prev",
  },
  breakpoints: {
    // when window width is >= 320px (phones)
    320: {
      slidesPerView: 1,
    },
    // when window width is >= 640px (small tablets)
    640: {
      slidesPerView: 2,
    },
    // when window width is >= 1024px (desktops)
    1124: {
      slidesPerView: 3,
    },
  },
});

const iconSwiper = new Swiper(".icon-slider", {
  direction: "horizontal",
  loop: true,

  spaceBetween: 16,
  navigation: {
    nextEl: ".swiper-custom-next",
    prevEl: ".swiper-custom-prev",
  },
  breakpoints: {
    320: { slidesPerView: 3 },
    768: { slidesPerView: 5 },
    1200: { slidesPerView: 9 },
  },
});

const productsSwiper = new Swiper(".products-swiper", {
  direction: "horizontal",
  spaceBetween: 10,
  watchOverflow: true,
  loop: true,
  slidesPerGroup: 1, // 🔥 Slide one by one

  rtl: true, // قد لا يعمل دائمًا، فاستخدم CSS direction أيضاً
  navigation: {
    nextEl: ".product-swiper-custom-next",
    prevEl: ".product-swiper-custom-prev",
  },
  breakpoints: {
    // when window width is >= 320px (phones)
    320: {
      slidesPerView: 2,
    },
    // when window width is >= 640px (small tablets)
    640: {
      slidesPerView: 2,
    },
    // when window width is >= 1024px (desktops)
    1124: {
      slidesPerView: 6,
    },
  },
});

const giftSwiper = new Swiper(".gift-swiper", {
  direction: "horizontal",
  loop: true,

  rtl: true, // قد لا يعمل دائمًا، فاستخدم CSS direction أيضاً
  navigation: {
    nextEl: ".gift-swiper-custom-next",
    prevEl: ".gift-swiper-custom-prev",
  },
  breakpoints: {
    // when window width is >= 320px (phones)
    320: {
      slidesPerView: 1,
    },
    // when window width is >= 640px (small tablets)
    640: {
      slidesPerView: 2,
    },
    // when window width is >= 1024px (desktops)
    1124: {
      slidesPerView: 7,
    },
  },
});

  const offersSwiper = new Swiper(".offers-swiper", {
    direction: "horizontal",
    loop: true,
    loopAdditionalSlides: 10,
    watchSlidesProgress: true,
    spaceBetween: 16,
    slidesPerGroup: 1,
    rtl: true, // هذه هي الإضافة الأساسية
    resistanceRatio: 0,
    touchReleaseOnEdges: true,
    freeMode: false, // تأكد أنها false
    speed: 300, // سرعة الانتقال
    touchRatio: 1, // حساسية اللمس
    simulateTouch: true, // تمكين السحب باللمس
    shortSwipes: true, // سوائب قصيرة
    longSwipes: false, // تعطيل السوائب الطويلة
    navigation: {
      nextEl: ".offers-swiper-custom-next",
      prevEl: ".offers-swiper-custom-prev",
    },
    breakpoints: {
      320: {
        slidesPerView: 2,
      },
      768: {
        slidesPerView: 5,
      },
      1124: {
        slidesPerView: 7,
      },
    },
  });

//

const tabs = document.querySelectorAll(".tab");
const items = document.querySelectorAll(".item");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    // تفعيل الزر الحالي
    tabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");

    const filter = tab.getAttribute("data-filter");

    items.forEach((item) => {
      if (filter === "all" || item.classList.contains(filter)) {
        item.style.display = "block";
      } else {
        item.style.display = "none";
      }
    });
  });
});
