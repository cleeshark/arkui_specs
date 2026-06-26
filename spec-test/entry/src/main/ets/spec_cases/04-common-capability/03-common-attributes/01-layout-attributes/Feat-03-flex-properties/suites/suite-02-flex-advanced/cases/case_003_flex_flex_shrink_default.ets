
@Entry
@Component
export struct Case003FlexFlexShrinkDefault {
  build() {
    // Flex default flexShrink is 1 - children should shrink to fit
    Flex({ direction: FlexDirection.Row }) {
      Text('A')
        .id('N_F03_S02_C003_TARGET_A')
        .width(150)
        .height(50)
        .backgroundColor('#FF9800')
      Text('B')
        .id('N_F03_S02_C003_TARGET_B')
        .width(150)
        .height(50)
        .backgroundColor('#9C27B0')
    }
    .id('N_F03_S02_C003_PARENT')
    .width(200)
    .height(100)
  }
}
