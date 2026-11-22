# Figure contract: show that separate seasonal calibration improves mean level
# but does not reproduce all spatial variability. All 42 available main-canal
# figure estimates are shown; station 27 diversion candidate is excluded.
# Quantitative grid, two panels, fixed shared scales, no interpolation of data.

base <- "chart_data"
summer_cv <- read.csv(file.path(base, "seasonal_cv_heldout.csv"),
                      fileEncoding = "UTF-8-BOM", check.names = FALSE)
summer_cv <- summer_cv[summer_cv$period == "2020-08", ]
summer_fit <- read.csv(file.path(base, "seasonal_final_fit.csv"),
                       fileEncoding = "UTF-8-BOM", check.names = FALSE)
summer_fit <- summer_fit[summer_fit$period == "2020-08", ]
winter_cv <- read.csv(file.path(base, "winter_inlet_heldout.csv"),
                      fileEncoding = "UTF-8-BOM", check.names = FALSE)
winter_fit <- read.csv(file.path(base, "winter_inlet_final_fit.csv"),
                       fileEncoding = "UTF-8-BOM", check.names = FALSE)
stopifnot(nrow(summer_cv) == 20, nrow(summer_fit) == 20,
          nrow(winter_cv) == 22, nrow(winter_fit) == 22,
          setequal(summer_cv$station_id, summer_fit$station_id),
          setequal(winter_cv$station_id, winter_fit$station_id))

panel_stats <- function(d) {
 y <- d$observed_ug_L_approx; pred <- d$heldout_prediction_ug_L
 sprintf("n = %d   CV RMSE %.2f   NSE %.2f", length(y), sqrt(mean((pred-y)^2)), 1-sum((pred-y)^2)/sum((y-mean(y))^2))
}

draw_figure <- function() {
  par(family = "Arial", mfrow = c(1, 2), mar = c(4.1, 4.4, 3.4, 0.8),
      oma = c(1.35, 0, 0.7, 0), fg = "#263746", col.axis = "#263746",
      col.lab = "#263746", cex.axis = 0.91, cex.lab = 1.0, bty = "l")
  panels <- list(list(cv = summer_cv, fit = summer_fit,
                      title = "a  Summer 2020 | separate calibration",
                      stat = panel_stats(summer_cv)),
                 list(cv = winter_cv, fit = winter_fit,
                      title = "b  Winter 2021 | inlet sensitivity",
                      stat = panel_stats(winter_cv)))
  for (panel in panels) {
    x <- panel$cv[order(panel$cv$distance_km), ]
    f <- panel$fit[order(panel$fit$distance_km), ]
    plot(x$distance_km, x$observed_ug_L_approx, xlim = c(0, 1300),
         ylim = c(0, 12), pch = 21, bg = "#67737C", col = "white", cex = 1.1,
         xlab = "Distance along canal (km)", ylab = "Chl-a (ug/L)",
         main = panel$title)
    grid(nx = NA, ny = NULL, col = "#E8ECEF")
    lines(f$distance_km, f$final_fitted_ug_L, col = "#184A68", lwd = 2.6)
    points(x$distance_km, x$heldout_prediction_ug_L, pch = 4,
           col = "#C56C30", lwd = 1.5, cex = 0.95)
    points(x$distance_km, x$observed_ug_L_approx, pch = 21,
           bg = "#67737C", col = "white", cex = 1.1)
    mtext(panel$stat, side = 3, line = 0.2, cex = 0.77, col = "#52616C")
    legend("topright", c("Digitized point", "Held-out prediction", "Full-data fit"),
           pch = c(21, 4, NA), pt.bg = c("#67737C", NA, NA),
           lty = c(NA, NA, 1), lwd = c(NA, 1.5, 2.6),
           col = c("#67737C", "#C56C30", "#184A68"),
           bty = "n", cex = 0.75, inset = 0.015)
  }
  mtext("Winter inlet setting was selected after reviewing the first parameter grid; both CV scores are exploratory.",
        outer = TRUE, side = 1, line = 0.25, cex = 0.7, col = "#6B7379")
}

stem <- file.path("04_figures", "Fig01_seasonal_spatial_calibration")
png(paste0(stem, ".png"), width = 9.1, height = 4.9, units = "in",
    res = 330, type = "cairo")
draw_figure(); dev.off()
cairo_pdf(paste0(stem, ".pdf"), width = 9.1, height = 4.9, family = "Arial")
draw_figure(); dev.off()
svg(paste0(stem, ".svg"), width = 9.1, height = 4.9, family = "Arial")
draw_figure(); dev.off()
