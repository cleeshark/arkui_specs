
@Entry
@Component
export struct Case001PositionXyBasic {
  build() {
    Stack() {
      Text('C001')
        .id('N_F02_C001_TARGET')
        .width(100)
        .height(50)
        .fontSize(16)
        .position({ x: 50, y: 30 })
    }
    .id('N_F02_C001_PARENT')
    .width(300)
    .height(300)
  }
}
