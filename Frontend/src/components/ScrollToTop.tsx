import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const ScrollToTop = () => {
  const { pathname } = useLocation();

  useEffect(() => {
    // Small delay to ensure the route transition is complete
    const scrollToTop = () => {
      // Scroll to top when route changes
      window.scrollTo({
        top: 0,
        left: 0,
        behavior: "instant"
      });

      // Also scroll any main content containers to top
      const mainElement = document.querySelector("main");
      if (mainElement) {
        mainElement.scrollTop = 0;
      }

      // Find any other scrollable containers and reset them
      const scrollableElements = document.querySelectorAll("[data-scroll-container]");
      scrollableElements.forEach((element) => {
        element.scrollTop = 0;
      });
    };

    // Use setTimeout to ensure it runs after React has updated the DOM
    const timeoutId = setTimeout(scrollToTop, 0);

    return () => clearTimeout(timeoutId);
  }, [pathname]);

  return null;
};

export default ScrollToTop;
