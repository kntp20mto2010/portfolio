var gulp = require("gulp");
var sass = require("gulp-sass");
const sassGlob = require("gulp-sass-glob");

gulp.task("sass", function (done) {
    gulp.src("./mysite/app/static/**/*.scss")
        .pipe(sassGlob())
        .pipe(sass({ outputStyle: "expanded" }))
        .pipe(gulp.dest("./css"));
    done();
});

gulp.task("watch", function () {
    gulp.watch("./sass/**/*.scss", gulp.series(["sass"]))
});
