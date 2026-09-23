@Entry
@Component
export struct Case002ButtonCircle {
  build() {
    Button({ type: ButtonType.Circle })
      .id('N_BUTTON_US1_C002_TARGET')
      .width(64)
      .height(64)
  }
}
