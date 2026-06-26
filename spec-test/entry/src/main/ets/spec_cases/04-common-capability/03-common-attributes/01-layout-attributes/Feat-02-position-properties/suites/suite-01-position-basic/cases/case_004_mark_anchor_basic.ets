
@Entry
@Component
export struct Case004MarkAnchorBasic {
  build() {
    Stack() {
      Text('C004')
        .id('N_F02_C004_TARGET')
        .width(100)
        .height(50)
        .fontSize(16)
        .position({ x: 100, y: 50 })
        .markAnchor({ x: 50, y: 25 })
    }
    .id('N_F02_C004_PARENT')
    .width(300)
    .height(300)
  }
}
