@Entry
@Component
export struct Case003ButtonNormal {
  build() {
    Button('Submit', { type: ButtonType.Normal })
      .id('N_BUTTON_US1_C003_TARGET')
      .width(160)
      .height(48)
  }
}
