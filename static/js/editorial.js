if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const reveal = new IntersectionObserver((entries, observer) => {
    entries.forEach(({ target, isIntersecting }) => {
      if (!isIntersecting) return;
      observer.unobserve(target);
      target.animate(
        [{ transform: 'translateY(8px)' }, { transform: 'translateY(0)' }],
        { duration: 280, easing: 'ease-out' },
      );
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('.ls-course, .ls-editorial').forEach(section => reveal.observe(section));
}
