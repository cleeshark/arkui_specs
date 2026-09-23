@Entry
@Component
export struct Case001ButtonCapsule {
  build() {
    Button('Click', { type: ButtonType.Capsule })
      .id('N_BUTTON_US1_C001_TARGET')
      .width(160)
      .height(48)
  }
}
