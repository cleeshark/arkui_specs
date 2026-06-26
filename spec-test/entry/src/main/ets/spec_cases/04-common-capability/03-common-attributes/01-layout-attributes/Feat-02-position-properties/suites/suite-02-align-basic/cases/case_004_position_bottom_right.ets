
@Entry
@Component
export struct Case004PositionBottomRight {
  build() {
    Stack() {
      Text('BR')
        .id('N_F02_S02_C004_TARGET')
        .width(80)
        .height(40)
        .position({ bottom: 10, right: 10 })
        .backgroundColor('#9C27B0')
    }
    .id('N_F02_S02_C004_PARENT')
    .width(300)
    .height(200)
    .backgroundColor('#E0E0E0')
  }
}
