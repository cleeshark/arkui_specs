
@Entry
@Component
export struct Case003OffsetBasic {
  build() {
    Stack() {
      Text('C003')
        .id('N_F02_C003_TARGET')
        .width(80)
        .height(40)
        .fontSize(16)
        .offset({ x: 20, y: 10 })
    }
    .id('N_F02_C003_PARENT')
    .width(300)
    .height(300)
    .align(Alignment.TopStart)
  }
}
