
@Entry
@Component
export struct Case002RowFlexShrinkDefault {
  build() {
    // Row default flexShrink is 0 - children should overflow, not shrink
    Row() {
      Text('A')
        .id('N_F03_S02_C002_TARGET_A')
        .width(150)
        .height(50)
        .backgroundColor('#4CAF50')
      Text('B')
        .id('N_F03_S02_C002_TARGET_B')
        .width(150)
        .height(50)
        .backgroundColor('#2196F3')
    }
    .id('N_F03_S02_C002_PARENT')
    .width(200)
    .height(100)
  }
}
