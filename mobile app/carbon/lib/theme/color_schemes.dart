import "package:flutter/material.dart";

class MaterialTheme {
  final TextTheme textTheme;

  const MaterialTheme(this.textTheme);

  static ColorScheme lightHighContrastScheme() {
    return const ColorScheme(
      brightness: Brightness.light,
      primary: Color(0xff2d2c2d),
      surfaceTint: Color(0xff605e5f),
      onPrimary: Color(0xffffffff),
      primaryContainer: Color(0xff4a494a),
      onPrimaryContainer: Color(0xffffffff),
      secondary: Color(0xff372921),
      onSecondary: Color(0xffffffff),
      secondaryContainer: Color(0xff56463c),
      onSecondaryContainer: Color(0xffffffff),
      tertiary: Color(0xff3e2712),
      onTertiary: Color(0xffffffff),
      tertiaryContainer: Color(0xff5f432d),
      onTertiaryContainer: Color(0xffffffff),
      error: Color(0xff600004),
      onError: Color(0xffffffff),
      errorContainer: Color(0xff98000a),
      onErrorContainer: Color(0xffffffff),
      surface: Color(0xfffff8f5),
      onSurface: Color(0xff000000),
      onSurfaceVariant: Color(0xff000000),
      outline: Color(0xff332a25),
      outlineVariant: Color(0xff514741),
      shadow: Color(0xff000000),
      scrim: Color(0xff000000),
      inverseSurface: Color(0xff33302e),
      inversePrimary: Color(0xffc9c5c7),
      primaryFixed: Color(0xff4a494a),
      onPrimaryFixed: Color(0xffffffff),
      primaryFixedDim: Color(0xff333233),
      onPrimaryFixedVariant: Color(0xffffffff),
      secondaryFixed: Color(0xff56463c),
      onSecondaryFixed: Color(0xffffffff),
      secondaryFixedDim: Color(0xff3e3027),
      onSecondaryFixedVariant: Color(0xffffffff),
      tertiaryFixed: Color(0xff5f432d),
      onTertiaryFixed: Color(0xffffffff),
      tertiaryFixedDim: Color(0xff462d18),
      onTertiaryFixedVariant: Color(0xffffffff),
      surfaceDim: Color(0xffbdb7b5),
      surfaceBright: Color(0xfffff8f5),
      surfaceContainerLowest: Color(0xffffffff),
      surfaceContainerLow: Color(0xfff6efec),
      surfaceContainer: Color(0xffe8e1de),
      surfaceContainerHigh: Color(0xffd9d3d0),
      surfaceContainerHighest: Color(0xffcbc5c3),
    );
  }

  ThemeData lightHighContrast() {
    return theme(lightHighContrastScheme());
  }

  static ColorScheme darkHighContrastScheme() {
    return const ColorScheme(
      brightness: Brightness.dark,
      primary: Color(0xfffffdff),
      surfaceTint: Color(0xffc9c5c7),
      onPrimary: Color(0xff000000),
      primaryContainer: Color(0xffe4e0e1),
      onPrimaryContainer: Color(0xff2a292a),
      secondary: Color(0xffffece2),
      onSecondary: Color(0xff000000),
      secondaryContainer: Color(0xffd6c0b3),
      onSecondaryContainer: Color(0xff160c05),
      tertiary: Color(0xffffede1),
      onTertiary: Color(0xff000000),
      tertiaryContainer: Color(0xffe2bb9d),
      onTertiaryContainer: Color(0xff170700),
      error: Color(0xffffece9),
      onError: Color(0xff000000),
      errorContainer: Color(0xffffaea4),
      onErrorContainer: Color(0xff220001),
      surface: Color(0xff151312),
      onSurface: Color(0xffffffff),
      onSurfaceVariant: Color(0xffffffff),
      outline: Color(0xfffdede4),
      outlineVariant: Color(0xffcec0b8),
      shadow: Color(0xff000000),
      scrim: Color(0xff000000),
      inverseSurface: Color(0xffe8e1de),
      inversePrimary: Color(0xff494748),
      primaryFixed: Color(0xffe5e1e2),
      onPrimaryFixed: Color(0xff000000),
      primaryFixedDim: Color(0xffc9c5c7),
      onPrimaryFixedVariant: Color(0xff111112),
      secondaryFixed: Color(0xfff5ded0),
      onSecondaryFixed: Color(0xff000000),
      secondaryFixedDim: Color(0xffd8c2b5),
      onSecondaryFixedVariant: Color(0xff190f07),
      tertiaryFixed: Color(0xffffdcc2),
      onTertiaryFixed: Color(0xff000000),
      tertiaryFixedDim: Color(0xffe6bfa1),
      onTertiaryFixedVariant: Color(0xff1f0c00),
      surfaceDim: Color(0xff151312),
      surfaceBright: Color(0xff534f4d),
      surfaceContainerLowest: Color(0xff000000),
      surfaceContainerLow: Color(0xff221f1e),
      surfaceContainer: Color(0xff33302e),
      surfaceContainerHigh: Color(0xff3e3b39),
      surfaceContainerHighest: Color(0xff494644),
    );
  }

  ThemeData darkHighContrast() {
    return theme(darkHighContrastScheme());
  }


  ThemeData theme(ColorScheme colorScheme) => ThemeData(
     useMaterial3: true,
     brightness: colorScheme.brightness,
     colorScheme: colorScheme,
     textTheme: textTheme.apply(
       bodyColor: colorScheme.onSurface,
       displayColor: colorScheme.onSurface,
     ),
     scaffoldBackgroundColor: colorScheme.surface,
     canvasColor: colorScheme.surface,
  );


  List<ExtendedColor> get extendedColors => [
  ];
}

class ExtendedColor {
  final Color seed, value;
  final ColorFamily light;
  final ColorFamily lightHighContrast;
  final ColorFamily lightMediumContrast;
  final ColorFamily dark;
  final ColorFamily darkHighContrast;
  final ColorFamily darkMediumContrast;

  const ExtendedColor({
    required this.seed,
    required this.value,
    required this.light,
    required this.lightHighContrast,
    required this.lightMediumContrast,
    required this.dark,
    required this.darkHighContrast,
    required this.darkMediumContrast,
  });
}

class ColorFamily {
  const ColorFamily({
    required this.color,
    required this.onColor,
    required this.colorContainer,
    required this.onColorContainer,
  });

  final Color color;
  final Color onColor;
  final Color colorContainer;
  final Color onColorContainer;
}
