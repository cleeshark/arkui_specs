@Entry
@Component
export struct Case004ButtonRoundedRectangle {
  build() {
    Button('Rounded', { type: ButtonType.ROUNDED_RECTANGLE })
      .id('N_BUTTON_US1_C004_TARGET')
      .width(160)
      .height(48)
  }
}
